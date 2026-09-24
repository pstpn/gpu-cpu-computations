#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

// Counts PMU events for the main thread of a program via the private kperf framework.
// Loaded into the target with DYLD_INSERT_LIBRARIES (see ./mperf), events come from MPERF_EVENTS.

#define KPC_MAX_COUNTERS 32
#define KPC_CLASS_CONFIGURABLE_MASK (1u << 1)

typedef struct kpep_db kpep_db;
typedef struct kpep_config kpep_config;
typedef struct kpep_event kpep_event;

static int (*kpc_set_counting)(uint32_t classes);
static int (*kpc_set_thread_counting)(uint32_t classes);
static int (*kpc_set_config)(uint32_t classes, uint64_t *config);
static int (*kpc_get_thread_counters)(uint32_t tid, uint32_t buf_count, uint64_t *buf);
static int (*kpc_force_all_ctrs_set)(int val);
static int (*kpc_force_all_ctrs_get)(int *val_out);

static int (*kpep_db_create)(const char *name, kpep_db **db_ptr);
static int (*kpep_db_event)(kpep_db *db, const char *name, kpep_event **ev_ptr);
static int (*kpep_config_create)(kpep_db *db, kpep_config **cfg_ptr);
static int (*kpep_config_force_counters)(kpep_config *cfg);
static int (*kpep_config_add_event)(kpep_config *cfg, kpep_event **ev_ptr, uint32_t flag, uint32_t *err);
static int (*kpep_config_kpc)(kpep_config *cfg, uint64_t *buf, size_t buf_size);
static int (*kpep_config_kpc_count)(kpep_config *cfg, size_t *count_ptr);
static int (*kpep_config_kpc_classes)(kpep_config *cfg, uint32_t *classes_ptr);
static int (*kpep_config_kpc_map)(kpep_config *cfg, size_t *buf, size_t buf_size);

static int event_count;
static char *event_names[KPC_MAX_COUNTERS];
static size_t counter_map[KPC_MAX_COUNTERS];
static uint64_t counters_start[KPC_MAX_COUNTERS];
static int counting;

static void fail(const char *msg, const char *arg) {
    fprintf(stderr, "mperf: %s%s\n", msg, arg ? arg : "");
    _exit(1);
}

#define LOAD(lib, fn) \
    if (!(*(void **)&fn = dlsym(lib, #fn))) fail("symbol not found: ", #fn)

static void load_frameworks(void) {
    void *kperf = dlopen("/System/Library/PrivateFrameworks/kperf.framework/kperf", RTLD_LAZY);
    void *kperfdata = dlopen("/System/Library/PrivateFrameworks/kperfdata.framework/kperfdata", RTLD_LAZY);
    if (!kperf || !kperfdata) fail("cannot load kperf frameworks", NULL);

    LOAD(kperf, kpc_set_counting);
    LOAD(kperf, kpc_set_thread_counting);
    LOAD(kperf, kpc_set_config);
    LOAD(kperf, kpc_get_thread_counters);
    LOAD(kperf, kpc_force_all_ctrs_set);
    LOAD(kperf, kpc_force_all_ctrs_get);

    LOAD(kperfdata, kpep_db_create);
    LOAD(kperfdata, kpep_db_event);
    LOAD(kperfdata, kpep_config_create);
    LOAD(kperfdata, kpep_config_force_counters);
    LOAD(kperfdata, kpep_config_add_event);
    LOAD(kperfdata, kpep_config_kpc);
    LOAD(kperfdata, kpep_config_kpc_count);
    LOAD(kperfdata, kpep_config_kpc_classes);
    LOAD(kperfdata, kpep_config_kpc_map);
}

__attribute__((constructor)) static void mperf_start(void) {
    const char *spec = getenv("MPERF_EVENTS");
    if (!spec || !*spec) return;

    char *list = strdup(spec);
    for (char *save, *name = strtok_r(list, ",", &save); name; name = strtok_r(NULL, ",", &save)) {
        if (event_count == KPC_MAX_COUNTERS) fail("too many events", NULL);
        event_names[event_count++] = name;
    }

    load_frameworks();

    kpep_db *db = NULL;
    kpep_config *cfg = NULL;
    if (kpep_db_create(NULL, &db)) fail("cannot load PMU event database", NULL);
    if (kpep_config_create(db, &cfg)) fail("cannot create PMU config", NULL);
    if (kpep_config_force_counters(cfg)) fail("cannot force counters", NULL);

    for (int i = 0; i < event_count; i++) {
        kpep_event *ev = NULL;
        if (kpep_db_event(db, event_names[i], &ev)) fail("unknown event: ", event_names[i]);
        if (kpep_config_add_event(cfg, &ev, 0, NULL)) fail("no free counter for event: ", event_names[i]);
    }

    uint32_t classes = 0;
    size_t reg_count = 0;
    uint64_t regs[KPC_MAX_COUNTERS] = {0};
    if (kpep_config_kpc_classes(cfg, &classes) ||
        kpep_config_kpc_count(cfg, &reg_count) ||
        kpep_config_kpc_map(cfg, counter_map, sizeof(counter_map)) ||
        kpep_config_kpc(cfg, regs, sizeof(regs)))
        fail("cannot build counter config", NULL);

    int force = 0;
    if (kpc_force_all_ctrs_get(&force)) fail("permission denied, run with sudo", NULL);
    if (kpc_force_all_ctrs_set(1)) fail("cannot take PMU counters", NULL);
    if ((classes & KPC_CLASS_CONFIGURABLE_MASK) && reg_count && kpc_set_config(classes, regs))
        fail("cannot set counter config", NULL);
    if (kpc_set_counting(classes) || kpc_set_thread_counting(classes))
        fail("cannot start counting", NULL);

    counting = 1;
    kpc_get_thread_counters(0, KPC_MAX_COUNTERS, counters_start);
}

__attribute__((destructor)) static void mperf_stop(void) {
    if (!counting) return;

    uint64_t counters_end[KPC_MAX_COUNTERS] = {0};
    kpc_get_thread_counters(0, KPC_MAX_COUNTERS, counters_end);

    kpc_set_counting(0);
    kpc_set_thread_counting(0);
    kpc_force_all_ctrs_set(0);

    fprintf(stderr, "\n Performance counter stats (mperf):\n\n");
    for (int i = 0; i < event_count; i++) {
        size_t idx = counter_map[i];
        fprintf(stderr, "%20llu  %s\n", counters_end[idx] - counters_start[idx], event_names[i]);
    }
    fprintf(stderr, "\n");
}
