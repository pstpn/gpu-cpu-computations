PDFLATEX ?= /usr/local/bin/pdflatex
FLAGS = -interaction=nonstopmode -halt-on-error -file-line-error -synctex=1

SOURCES = report/report.tex $(wildcard report/chapters/*.tex) $(wildcard report/data/*) $(wildcard scripts/*.py)
BINARIES = daxpy daxpy_float branch_test libmperf.dylib

.PHONY: all report clean

report: report/report.pdf

report/report.pdf: $(SOURCES)
	cd report && $(PDFLATEX) $(FLAGS) report.tex
	cd report && $(PDFLATEX) $(FLAGS) report.tex
	cd report && $(PDFLATEX) $(FLAGS) report.tex

all: $(BINARIES) report

daxpy: daxpy.cpp
	g++ daxpy.cpp -O3 -std=c++17 -o daxpy

daxpy_float: daxpy.cpp
	g++ daxpy.cpp -O3 -std=c++17 -DTYPE=float -o daxpy_float

branch_test: branch_test.cpp
	g++ branch_test.cpp -O3 -std=c++17 -o branch_test

libmperf.dylib: mperf.c
	clang -O2 -Wall -dynamiclib mperf.c -o libmperf.dylib

clean:
	rm -f $(BINARIES) events.txt
	rm -rf scripts/__pycache__
	cd report && rm -f *.aux *.bbl *.bcf *.blg *.fdb_latexmk *.fls *.lof *.lot *.log *.out *.run.xml *.synctex.gz *.toc
