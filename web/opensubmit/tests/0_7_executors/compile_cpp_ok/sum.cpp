#include <pthread.h>
#include <inttypes.h>
#include <assert.h>
#include <stdio.h>
#include <iostream>
#include <fstream>
#include <stdlib.h>

using namespace std;

#define BASE2        2
#define BASE10       10
#define BASE2DIGITS  64
#define BASE10DIGITS 40
#define MIN_THREADS  1

#ifndef UINT64_MAX
#define UINT64_MAX 0xffffffffffffffffULL
#endif

uint64_t START     = 0;
uint64_t END       = 0;
uint64_t REAL_END  = 0;
uint64_t THREADS   = 0;

typedef struct {
	uint32_t id;
	uint64_t high;
	uint64_t low;
} SumArgument;

void * sum(void *args) {
	SumArgument *arg = (SumArgument *) args;
	uint32_t id = arg->id;
	uint64_t high = 0;
	//uint64_t low = 0;
	uint64_t low  = END + id < REAL_END ? END + id : 0;

	// sum every THREAD'th number starting with your own id (other numbers are done by other threads)
	for (uint64_t i = START + id; i <= END; i += THREADS) {
		asm volatile("addq %[ai], %[alow];"
					 "adcq $0, %[ahigh];"
					 : [alow] "+r" (low), [ahigh] "+r" (high)
					 : [ai] "r" (i):);
	}
	arg->high = high;
	arg->low  = low;

	return NULL;
}

void print(uint64_t high, uint64_t low) {
	ofstream out("output.txt");

	// only 64 bit part set? print normally
	if (not high) {
		out << low << endl;
		out.close();
		return;
	} 

	char digits[BASE10DIGITS] = {0};

	// high part
	for (int i = BASE2DIGITS - 1; i > -1; --i) {
		if (high >> i & 1) ++digits[0];

		for (int j = 0; j < BASE10DIGITS; ++j) {
			digits[j] *= BASE2;
		}
		for (int j = 0; j < BASE10DIGITS - 1; ++j) {
			digits[j + 1] += digits[j] / BASE10;
			digits[j] %= BASE10;
		}
	}

	// low part
	for (int i = BASE2DIGITS - 1; i > -1; --i) {
		if (low >> i & 1) ++digits[0];

		for (int j = 0; j < BASE10DIGITS; ++j) {
			if (not i) break;
			digits[j] *= BASE2;
		}
		for (int j = 0; j < BASE10DIGITS - 1; ++j) {
			digits[j + 1] += digits[j] / BASE10;
			digits[j] %= BASE10;
		}
	}

	// print
	bool found = false;
	for (int i = BASE10DIGITS - 1; i > -1; --i) {
		if (digits[i] == 0 && not found) continue;
		found = true;
		out << digits[i];
	}
	out << endl;
	out.close();
}

int main(int argc, char **argv) {
	// check argument count
	if (argc != 4) {
		cout << "Usage: " << argv[0] << " THREADS START END" << endl;
		exit(1);
	}

    cout << "Starting output to output.txt" << endl;
    
	// parse command line parameters
	sscanf(argv[1], "%llu", (long long unsigned int*)&THREADS);
	sscanf(argv[2], "%llu", (long long unsigned int*)&START);
	sscanf(argv[3], "%llu", (long long unsigned int*)&REAL_END);

	// check for sane parameters
	assert(THREADS >= MIN_THREADS);
	assert(START <= REAL_END);

	// prevent overflow on edge cases (e.g. UINT64_MAX + THREADS == THREADS)
	END = UINT64_MAX - REAL_END >= THREADS ? REAL_END : REAL_END - THREADS;

	// Allocate memory
	SumArgument *arguments = (SumArgument *) malloc(THREADS * sizeof(SumArgument));
	pthread_t *threads = (pthread_t *) malloc(THREADS * sizeof(pthread_t));

	// create threads
	SumArgument *arg = NULL;
	for (uint32_t i = 1; i < THREADS; ++i) {
		arg = &arguments[i];
		arg->id = i;
		pthread_create(&threads[i], NULL, sum, arg);
	}
	
	// do some useful stuff (main thread is considered as thread ID 0)
  arguments[0].id = 0;
  sum((void *)&arguments[0]);

	// join threads
	uint64_t high = 0;
	uint64_t low  = 0;
	for (uint32_t i = 0; i < THREADS; ++i) {
		arg = &arguments[i];
		pthread_join(threads[i], NULL);
		asm volatile("addq %[aolow], %[alow];"
					 "adcq %[aohigh], %[ahigh];"
					 : [alow] "+r" (low), [ahigh] "+r" (high)
					 : [aolow] "r" (arg->low), [aohigh] "r" (arg->high):);
	}
	
	print(high, low);

	// Free memory
	free(arguments);
	free(threads);

	return 0;
}