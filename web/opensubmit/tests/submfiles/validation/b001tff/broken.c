/* AuP WS 2016/17, Bonusaufgabe 2 */

int printf(const char*, ...);
int atoi(const char*);
int reverse(int n, int x, int y);

// Deklaration der Umkehrfunktion
int reverse(int n, int x, int y=0){
	if (n) return 
	x=n%10;
	y=y*10+x;
	reverse(n/10);
}

int main(int carg, const char **varg) {
  // ein Parameter uebergeben?
  if (carg != 2) return -1;
  // gib den berechneten Wert aus
  printf("%d\n",reverse(atoi(varg[1])));
  // Rueckgabewert 0 bedeutet: alles okay
  return 0;
}


