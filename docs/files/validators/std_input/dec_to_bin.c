#include <stdlib.h>
#include <stdio.h>

char *create_binary(int decimal)
{
    char *binary;
    int length = 0;
    int tmp_decimal = decimal;
    
    while (tmp_decimal > 0)
    {
        tmp_decimal = tmp_decimal / 2;
        length++;
    }

    binary = malloc(length * sizeof(char) + 1);

    for (int i = length-1; i >= 0; i--)
    {
        binary[i] = decimal % 2 + '0';
        decimal = decimal / 2;
    }
    
    binary[length] = '\0';

    return binary;
}

int main(void)
{
    int number;
    char *binary;

    scanf("%d", &number);
    binary = create_binary(number);
    printf("%s\n", binary);
    free(binary);

    return 0;
}