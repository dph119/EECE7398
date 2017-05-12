#include <stdio.h>
#define N 700
#define LOOP 10
int main()
{
  double a[N][N]; /* input matrix */
  double b[N][N]; /* input matrix */
  double c[N][N]; /* result matrix */
  int i,j,k,p;

  for(p=0; p<LOOP; p++)
    {

      /* initialize */
      for(i=0; i<N; i++){    
	for(j=0; j<N; j++){
	  a[i][j] = (double)(i+j);
	  b[i][j] = (double)(i-j);
	}
      }
      printf("starting multiply \n");

      for(i=0; i<N; i++){
	for(j=0; j<N; j++){
	  c[i][j] = 0.0;
	front:
	  for(k=0; k<N; k++){  /* how many instructions are in this loop? */
	    c[i][j] = c[i][j] + a[i][k]*b[k][j]; /* most time spent here! */
	    /* this loop is executed one million times */
	  }
	back:;
	}
      }
      printf("a result %g \n", c[7][8]); /* prevent dead code elimination */
    }
  return 0;
}
