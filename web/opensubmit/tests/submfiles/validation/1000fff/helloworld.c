#include <stdio.h>

int main(int argc, char** argv) {
	char input[20];
	printf("Please provide your input: ");
	fgets(input, 20, stdin);
	printf("Your input was: %s", input);
	return 0;
}
