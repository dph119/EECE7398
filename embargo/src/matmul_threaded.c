#include <stdio.h>
#include <stdlib.h>
#include <pthread.h> 
#define N 700
#define LOOP 1

///////////////////////////////////////
// 
// Based off code from darts.c
// as well as pthread_create man page.
//
///////////////////////////////////////

volatile long double result = 0.0;
pthread_mutex_t resultLock;    /* how we synchronize writes to 'result' */
long double intervals;         /* how finely we chop the integration */
int numThreads;                /* how many threads we use */
double a[N][N]; /* input matrix */
double b[N][N]; /* input matrix */
double c[N][N]; /* result matrix */

struct thread_info {          /* Used as argument to thread_start() */
  pthread_t thread_id;        /* ID returned by pthread_create() */
  int       thread_num;       /* Application-defined thread # */
  int       perThread;
  int       threadStart;
  int       i, j;
};

void *matmul(void *arg){
  int i,j,k;
  double mult = 0;
  int perThread, threadStart;
  struct thread_info *tinfo = arg;
  
  perThread   = tinfo->perThread;
  threadStart = tinfo->threadStart;
  i           = tinfo->i;
  j           = tinfo->j;

  //  printf("perThread = %d, threadStart = %d\n", tinfo->perThread, tinfo->threadStart);
  for (k = tinfo->threadStart; k < tinfo->perThread + tinfo->threadStart; k++){
    // Not need for mutext since we're just readin the values
    mult += a[i][k]*b[k][j]; /* most time spent here! */
  }
  
  // Result is under mutext since multiple threads will be adding to it
  pthread_mutex_lock(&resultLock);
  result += mult;
  pthread_mutex_unlock(&resultLock);
  return NULL;
}

int main()
{

  pthread_t *threads;        /* dynarray of threads */
  void *retval;              /* unused; required for join() */
  int *threadID;             /* dynarray of thread id #s */
  int p;                     /* loop control variable */
  int i,j,k;
  int numThreads = 1;
  struct thread_info *tinfo;

  threads  = malloc(numThreads*sizeof(pthread_t));
  threadID = malloc(numThreads*sizeof(int));
  tinfo    = calloc(numThreads, sizeof(struct thread_info));
  pthread_mutex_init(&resultLock, NULL);

  ///////////////////////////////////////////

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
	  result = c[i][j];

	  // Make a thread run this, sharing c[i][j]
	  // Divide N across M threads
	  for(k=0; k<numThreads; k++){  /* how many instructions are in this loop? */
	    // Set a bunch of state for each thread so they know what part of each matrix
	    // they're responsible for.
	    tinfo[k].thread_num  = k;
	    tinfo[k].perThread   = N / numThreads;
	    tinfo[k].threadStart = tinfo[k].perThread*k;
	    tinfo[k].i           = i;
	    tinfo[k].j           = j;
	    // Each thread is responsible for MACC'ing a part of the matrix, storing
	    // its sum in the variable "result".
	    // Once all threads complete, result is then copied over to c[i][j]
	    pthread_create(&threads[k], NULL, matmul, &tinfo[k]);
	  }
	  for (k = 0; k < numThreads; k++) {
	    pthread_join(threads[k], &retval);
	  }	  
	  c[i][j] = result;
	}
      }
      printf("a result %g \n", c[7][8]); /* prevent dead code elimination */
    }
  return 0;
}
