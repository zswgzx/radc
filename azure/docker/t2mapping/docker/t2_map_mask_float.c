/* Bob: This program is intended to create T2 maps based on nii files given to it representing different echo times. Based on the T2 maps, it can also create a simplistic tissue mask for the volume and can generate a "simulated TE" volume, with the user specifying the simulated TE in ms (typically I have used 0.0 ms). This input volumes must be in nii format. The rest of the command line inputs are explained once you type the program name. As always, inspect this program carefully before each use; it is put together quickly. Particular, inspect the weighting assigned to each datapoint via the vector 'devs'. I really haven't been able to tell if that is the appropriate way to weight each datapoint.*/

/* Shengwei: made changes to 1) remove inputs ID and T2 cutoff and output simte, 2) made output of t2vol in datatype float and add chi2 & pdw (simte=0) as output, 3) assume no weights for fitting, and 4) slightly change masking criteria */

/* compile by 'gcc t2_map_mask_float.c -o t2_map_mask_float -lm -g -Wall' on Ubuntu linux */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <math.h>

#define PDwthresh 100
#define T2thresh 1e4
#define NR_END 1
#define FREE_ARG char*
#define TRUE 1
#define FALSE 0
static float sqrarg;
#define SQR(a) ((sqrarg=(a)) == 0.0 ? 0.0 : sqrarg*sqrarg)

float *vector_float(long nl, long nh);
void free_vector_float(float *v, long nl, long nh);
float ****d4tensor_float(long nrl, long nrh, long ncl, long nch, long ndl, long ndh, long nfl, long nfh);
void free_d4tensor_float(float ****t, long nrl, long nrh, long ncl, long nch,long ndl, long ndh, long nfl, long nfh);
float ***d3tensor_float(long nrl, long nrh, long ncl, long nch, long ndl, long ndh);
void free_d3tensor_float(float ***t, long nrl, long nrh, long ncl, long nch, long ndl, long ndh);
void fit(float x[], float y[], int ndata, float sig[], int mwt, float *a, float *b, float *siga, float *sigb, float *chi2);

int main(int argc, char **argv)
{
  FILE *fpinput, *fpoutput, *fpmask,*fpchi2,*fppdw;
  float ftemp,a,b,siga,sigb,chi2,*echotimes,*vals,*devs,***chisq,***pdw,***simplemask,***t2,****echodata;
  char fname[64],ctemp;
  unsigned int numechoes,i,x,y,z;

  struct nifti_1_header 
  {                     /* NIFTI-1 usage         */  /* ANALYZE 7.5 field(s) */
                        /*************************/  /************************/
                                              /*--- was header_key substruct ---*/
    int   sizeof_hdr;    /*!< MUST be 348           */  /* int sizeof_hdr;      */
    char  data_type[10]; /*!< ++UNUSED++            */  /* char data_type[10];  */
    char  db_name[18];   /*!< ++UNUSED++            */  /* char db_name[18];    */
    int   extents;       /*!< ++UNUSED++            */  /* int extents;         */
    short session_error; /*!< ++UNUSED++            */  /* short session_error; */
    char  regular;       /*!< ++UNUSED++            */  /* char regular;        */
    char  dim_info;      /*!< MRI slice ordering.   */  /* char hkey_un0;       */
    
    /*--- was image_dimension substruct ---*/
    short dim[8];        /*!< Data array dimensions.*/  /* short dim[8];        */
    float intent_p1 ;    /*!< 1st intent parameter. */  /* short unused8;       */
    /* short unused9;       */
    float intent_p2 ;    /*!< 2nd intent parameter. */  /* short unused10;      */
    /* short unused11;      */
    float intent_p3 ;    /*!< 3rd intent parameter. */  /* short unused12;      */
    /* short unused13;      */
    short intent_code ;  /*!< NIFTI_INTENT_* code.  */  /* short unused14;      */
    short datatype;      /*!< Defines data type!    */  /* short datatype;      */
    short bitpix;        /*!< Number bits/voxel.    */  /* short bitpix;        */
    short slice_start;   /*!< First slice index.    */  /* short dim_un0;       */
    float pixdim[8];     /*!< Grid spacings.        */  /* float pixdim[8];     */
    float vox_offset;    /*!< Offset into .nii file */  /* float vox_offset;    */
    float scl_slope ;    /*!< Data scaling: slope.  */  /* float funused1;      */
    float scl_inter ;    /*!< Data scaling: offset. */  /* float funused2;      */
    short slice_end;     /*!< Last slice index.     */  /* float funused3;      */
    char  slice_code ;   /*!< Slice timing order.   */
    char  xyzt_units ;   /*!< Units of pixdim[1..4] */
    float cal_max;       /*!< Max display intensity */  /* float cal_max;       */
    float cal_min;       /*!< Min display intensity */  /* float cal_min;       */
    float slice_duration;/*!< Time for 1 slice.     */  /* float compressed;    */
    float toffset;       /*!< Time axis shift.      */  /* float verified;      */
    int   glmax;         /*!< ++UNUSED++            */  /* int glmax;           */
    int   glmin;         /*!< ++UNUSED++            */  /* int glmin;           */

    /*--- was data_history substruct ---*/
    char  descrip[80];   /*!< any text you like.    */  /* char descrip[80];    */
    char  aux_file[24];  /*!< auxiliary filename.   */  /* char aux_file[24];   */

    short qform_code ;   /*!< NIFTI_XFORM_* code.   */  /*-- all ANALYZE 7.5 ---*/
    short sform_code ;   /*!< NIFTI_XFORM_* code.   */  /*   fields below here  */
                                                        /*   are replaced       */
    float quatern_b ;    /*!< Quaternion b param.   */
    float quatern_c ;    /*!< Quaternion c param.   */
    float quatern_d ;    /*!< Quaternion d param.   */
    float qoffset_x ;    /*!< Quaternion x shift.   */
    float qoffset_y ;    /*!< Quaternion y shift.   */
    float qoffset_z ;    /*!< Quaternion z shift.   */

    float srow_x[4] ;    /*!< 1st row affine transform.   */
    float srow_y[4] ;    /*!< 2nd row affine transform.   */
    float srow_z[4] ;    /*!< 3rd row affine transform.   */

    char intent_name[16];/*!< 'name' or meaning of data.  */

    char magic[4] ;      /*!< MUST be "ni1\0" or "n+1\0". */
  } ;                   /**** 348 bytes total ****/

  typedef struct nifti_1_header nifti_1_header;
  nifti_1_header hdrinfo, hdrinfo1;

  /* command line inputs */
  if(argc<2)
    {	
      fprintf(stderr, "Incorrect usage.");
      fprintf(stderr, "\nTo use this program correctly provide the following arguments:");
      fprintf(stderr, "\n\nt2_map_mask_float <num. of echoes> <echo time(s) (in ms, as many as needed)>\n\n");
      fprintf(stderr,"NOTE: echo files HAVE TO be in FLOAT datatype and named 'echo00xx.nii', change {PDw,T2}thresh if needed.\n");
      exit(1);
    }

  numechoes = atoi(argv[1]);

  if(argc!=2+numechoes)
    {	
      fprintf(stderr, "Inconsistent # of t2 images.");
      fprintf(stderr, "\nTo use this program correctly provide the following arguments:");
      fprintf(stderr, "\n\nt2_map_mask_float <num. of echoes> <echo time(s) (in ms, as many as needed)>\n\n");
      fprintf(stderr,"NOTE: echo files HAVE TO be in FLOAT datatype and named 'echo00xx.nii', change {PDw,T2}thresh if needed.\n");
      exit(1);	
    }

  echotimes = vector_float(1, numechoes);
  vals = vector_float(1, numechoes); 
  devs = vector_float(1, numechoes);

  for(i=1; i<=numechoes; i++)	echotimes[i] = atof(argv[i+1]);

  fpinput = fopen("echo0000.nii", "rb");
  if(fpinput == NULL)
    {
      fprintf(stderr, "\nerror opening input file echo0000.nii");
      exit(1);
    }
  fread(&hdrinfo, sizeof(nifti_1_header), 1, fpinput); rewind(fpinput);
  fread(&hdrinfo1, sizeof(nifti_1_header), 1, fpinput);
  fclose(fpinput);

  echodata = d4tensor_float(1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3], 1, numechoes);

  pdw = d3tensor_float(1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3]);
  chisq = d3tensor_float(1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3]);
  t2 = d3tensor_float(1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3]);
  simplemask = d3tensor_float(1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3]); 

  hdrinfo1.datatype = 2;
  hdrinfo1.bitpix = 8;

  /* read in 4D echo data */
  for(i=0; i<numechoes; i++)
    {
      sprintf(fname, "echo%04d.nii", i);
      fpinput = fopen(fname, "rb");
      if(fpinput == NULL)
	{
	  fprintf(stderr, "\nerror opening input file %s", fname);
	  exit(1);
	}
      
      fseek(fpinput, hdrinfo.vox_offset, SEEK_SET);
      for(z=1;z<=hdrinfo.dim[3];z++)
	for(y=1;y<=hdrinfo.dim[2];y++)
	  for(x=1;x<=hdrinfo.dim[1];x++)
	    {
	      if(fread(&ftemp, sizeof(float), 1, fpinput) != 1)
		{
		  printf("\nError reading from file %s.\n", fname);
		  exit(1);
		}

	      echodata[x][y][z][i+1] = ftemp;

	      if(i == 0)
		simplemask[x][y][z] = ftemp;
	    }
	  
      fclose(fpinput);
    }

  fpoutput = fopen("t2vol.nii", "wb"); 
  if(fpoutput == NULL)
    {
      fprintf(stderr, "\nerror opening output file t2vol.nii");
      exit(1);
    }

  fpmask = fopen("mask.nii", "wb");
  if(fpmask == NULL)
    {
      fprintf(stderr, "\nerror opening output file mask.nii");
      exit(1);
    }

  fpchi2 = fopen("chi2.nii", "wb");
  if(fpchi2 == NULL)
    {
      fprintf(stderr, "\nerror opening output file chi2.nii");
      exit(1);
    }

  fppdw = fopen("pdw.nii", "wb");
  if(fpchi2 == NULL)
    {
      fprintf(stderr, "\nerror opening output file pdw.nii");
      exit(1);
    }

  fwrite(&hdrinfo, sizeof(nifti_1_header), 1, fpoutput);
  fseek(fpoutput, hdrinfo.vox_offset, SEEK_SET);
  fwrite(&hdrinfo1, sizeof(nifti_1_header), 1, fpmask);
  fseek(fpmask, hdrinfo.vox_offset, SEEK_SET);
  fwrite(&hdrinfo, sizeof(nifti_1_header), 1, fpchi2);
  fseek(fpchi2, hdrinfo.vox_offset, SEEK_SET);
  fwrite(&hdrinfo, sizeof(nifti_1_header), 1, fppdw);
  fseek(fppdw, hdrinfo.vox_offset, SEEK_SET);

  /* exponential fitting procedure */
  /* data is first linearized by taking log */
  /* weights are assigned using 'devs' so that early echoes count for their fair share just as much as later echoes */
  for(z=1;z<=hdrinfo.dim[3];z++)
    for(y=1;y<=hdrinfo.dim[2];y++)
      for(x=1;x<=hdrinfo.dim[1];x++)
	{
	  for(i=1; i<=numechoes; i++)
	    {
	      vals[i] = log(echodata[x][y][z][i]);

	      devs[i] = 1.0;
	    }

	  fit(echotimes, vals, numechoes, devs, 0, &a, &b, &siga, &sigb, &chi2);
	  
	  chisq[x][y][z]=chi2;
	  t2[x][y][z] = -1.0/b;
	  pdw[x][y][z]=exp(a);
	  	  
	  /* intensity based masking */
	  simplemask[x][y][z] = (simplemask[x][y][z] >= PDwthresh)?1:0;
	  ctemp=(simplemask[x][y][z] >0)?1:0;
	  
	  if (simplemask[x][y][z] != 0)// && t2[x][y][z] >=0 && t2[x][y][z] <=T2thresh)
	    ftemp = t2[x][y][z];
	  //else if (simplemask[x][y][z] != 0 && (t2[x][y][z] >= T2thresh || t2[x][y][z]<0))
	    //ftemp = T2thresh;
	  else
	    ftemp = 0;
	  
	  fwrite(&t2[x][y][z], sizeof(float), 1, fpoutput);
	  fwrite(&chisq[x][y][z], sizeof(float), 1, fpchi2);
	  fwrite(&ctemp, sizeof(char), 1, fpmask);
	  fwrite(&pdw[x][y][z], sizeof(float), 1, fppdw);
	  
	}
 
  fclose(fpchi2);  
  fclose(fpoutput);
  fclose(fpmask);
  fclose(fppdw);
  
  free_vector_float(echotimes,1,numechoes);
  free_vector_float(vals,1,numechoes);
  free_vector_float(devs,1,numechoes);

  free_d4tensor_float(echodata, 1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3], 1, numechoes);

  free_d3tensor_float(pdw,1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3]);
  free_d3tensor_float(chisq, 1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3]);
  free_d3tensor_float(t2,1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3]);
  free_d3tensor_float(simplemask,1, hdrinfo.dim[1], 1, hdrinfo.dim[2], 1, hdrinfo.dim[3]);
    
  return 0;
}

void nrerror(char error_text[])
/* Numerical Recipes standard error handler */
{
        fprintf(stderr,"Numerical Recipes run-time error...\n");
        fprintf(stderr,"%s\n",error_text);
        fprintf(stderr,"...now exiting to system...\n");
        exit(1);
}

float *vector_float(long nl, long nh)
/* allocate a double vector with subscript range v[nl..nh] */
{
        float *v;

        v=(float *)malloc((size_t) ((nh-nl+1+NR_END)*sizeof(float)));
        if (!v) nrerror("allocation failure in vector()");
        return v-nl+NR_END;
}

void free_vector_float(float *v, long nl, long nh)
/* free a double vector allocated with vector() */
{
        free((FREE_ARG) (v+nl-NR_END));
}

float ***d3tensor_float(long nrl, long nrh, long ncl, long nch, long ndl, long ndh)
/* allocate a float d3tensor with range t[nrl..nrh][ncl..nch][ndl..ndh] */
{
	long i,j,nrow=nrh-nrl+1,ncol=nch-ncl+1,ndep=ndh-ndl+1;
	float ***t;

	/* allocate pointers to pointers to rows */
	t=(float ***) malloc((size_t)((nrow+NR_END)*sizeof(float**)));
	if (!t) nrerror("allocation failure 1 in s3tensor()");
	t += NR_END;
	t -= nrl;

	/* allocate pointers to rows and set pointers to them */
	t[nrl]=(float **) malloc((size_t)((nrow*ncol+NR_END)*sizeof(float*)));
	if (!t[nrl]) nrerror("allocation failure 2 in s3tensor()");
	t[nrl] += NR_END;
	t[nrl] -= ncl;

	/* allocate rows and set pointers to them */
	t[nrl][ncl]=(float *) malloc((size_t)((nrow*ncol*ndep+NR_END)*sizeof(float)));
	if (!t[nrl][ncl]) nrerror("allocation failure 3 in s3tensor()");
	t[nrl][ncl] += NR_END;
	t[nrl][ncl] -= ndl;

	for(j=ncl+1;j<=nch;j++) t[nrl][j]=t[nrl][j-1]+ndep;
	for(i=nrl+1;i<=nrh;i++) {
		t[i]=t[i-1]+ncol;
		t[i][ncl]=t[i-1][ncl]+ncol*ndep;
		for(j=ncl+1;j<=nch;j++) t[i][j]=t[i][j-1]+ndep;
	}

	/* return pointer to array of pointers to rows */
	return t;
}

void free_d3tensor_float(float ***t, long nrl, long nrh, long ncl, long nch, long ndl, long ndh)
/* free a float d3tensor allocated by d3tensor() */
{
	free((FREE_ARG) (t[nrl][ncl]+ndl-NR_END));
	free((FREE_ARG) (t[nrl]+ncl-NR_END));
	free((FREE_ARG) (t+nrl-NR_END));
}

float ****d4tensor_float(long nrl, long nrh, long ncl, long nch, long ndl, long ndh, long nfl, long nfh)
/* allocate a double 4tensor with range t[nrl..nrh][ncl..nch][ndl..ndh][nfl..nfh] */
{
	long i,j,k,nrow=nrh-nrl+1,ncol=nch-ncl+1,ndep=ndh-ndl+1,nf=nfh-nfl+1;
	float ****t;

	/* allocate pointers to pointers to pointers to rows */
	t=(float ****) malloc((size_t)((nrow+NR_END)*sizeof(float***)));
	if (!t) nrerror("allocation failure 1 in d4tensor()");
	t += NR_END;
	t -= nrl;

	/* allocate pointers to pointers to rows */
	t[nrl]=(float ***) malloc((size_t)((nrow*ncol+NR_END)*sizeof(float**)));
	if (!t[nrl]) nrerror("allocation failure 2 in d4tensor()");
	t[nrl] += NR_END;
	t[nrl] -= ncl;

	/* allocate pointers to rows and set pointers to them */
	t[nrl][ncl]=(float **) malloc((size_t)((nrow*ncol*ndep+NR_END)*sizeof(float*)));
	if (!t[nrl][ncl]) nrerror("allocation failure 3 in d4tensor()");
	t[nrl][ncl] += NR_END;
	t[nrl][ncl] -= ndl;

	/* allocate rows and set pointers to them */
	t[nrl][ncl][ndl]=(float *) malloc((size_t)((nrow*ncol*ndep*nf+NR_END)*sizeof(float)));
	if (!t[nrl][ncl][ndl]) nrerror("allocation failure 4 in d4tensor()");
	t[nrl][ncl][ndl] += NR_END;
	t[nrl][ncl][ndl] -= nfl;

	for(i=nrl+1;i<=nrh;i++)
		t[i]=t[i-1]+ncol;

	for(i=nrl+1;i<=nrh;i++)
		t[i][ncl]=t[i-1][ncl]+ncol*ndep;
	for(i=nrl;i<=nrh;i++)
    	for(j=ncl+1;j<=nch;j++)
			t[i][j]=t[i][j-1]+ndep;

    for(j=nrl+1;j<=nrh;j++) 
		t[j][ncl][ndl]=t[j-1][ncl][ndl]+ncol*ndep*nf;
	for(i=nrl;i<=nrh;i++)
		for(j=ncl+1;j<=nch;j++) 
			t[i][j][ndl]=t[i][j-1][ndl]+ndep*nf;
		
	for(i=nrl;i<=nrh;i++) 
		for(j=ncl;j<=nch;j++) 
			for(k=ndl+1;k<=ndh;k++) 
				t[i][j][k]=t[i][j][k-1]+nf;

	return t;
}

void free_d4tensor_float(float ****t, long nrl, long nrh, long ncl, long nch,
	long ndl, long ndh, long nfl, long nfh)
/* free a double d4tensor allocated by d4tensor() */
{
	free((FREE_ARG) (t[nrl][ncl][ndl]+nfl-NR_END));
	free((FREE_ARG) (t[nrl][ncl]+ndl-NR_END));
	free((FREE_ARG) (t[nrl]+ncl-NR_END));
	free((FREE_ARG) (t+nrl-NR_END));
}

#define NRANSI

void fit(float x[], float y[], int ndata, float sig[], int mwt, float *a,
	float *b, float *siga, float *sigb, float *chi2)
{
	float gammq(float a, float x);
	int i;
	float wt,t,sxoss,sx=0.0,sy=0.0,st2=0.0,ss,sigdat;

	*b=0.0;
	if (mwt) {
		ss=0.0;
		for (i=1;i<=ndata;i++) {
			wt=1.0/SQR(sig[i]);
			ss += wt;
			sx += x[i]*wt;
			sy += y[i]*wt;
		}
	} else {
		for (i=1;i<=ndata;i++) {
			sx += x[i];
			sy += y[i];
		}
		ss=ndata;
	}
	sxoss=sx/ss;
	if (mwt) {
		for (i=1;i<=ndata;i++) {
			t=(x[i]-sxoss)/sig[i];
			st2 += t*t;
			*b += t*y[i]/sig[i];
		}
	} else {
		for (i=1;i<=ndata;i++) {
			t=x[i]-sxoss;
			st2 += t*t;
			*b += t*y[i];
		}
	}
	*b /= st2;
	*a=(sy-sx*(*b))/ss;
	*siga=sqrt((1.0+sx*sx/(ss*st2))/ss);
	*sigb=sqrt(1.0/st2);
	*chi2=0.0;
	if (mwt == 0) {
		for (i=1;i<=ndata;i++)
			*chi2 += SQR(y[i]-(*a)-(*b)*x[i]);
		sigdat=sqrt((*chi2)/(ndata-2));
		*siga *= sigdat;
		*sigb *= sigdat;
	} else {
		for (i=1;i<=ndata;i++)
			*chi2 += SQR((y[i]-(*a)-(*b)*x[i])/sig[i]);
	}
}
#undef NRANSI


float gammq(float a, float x)
{
	void gcf(float *gammcf, float a, float x, float *gln);
	void gser(float *gamser, float a, float x, float *gln);
	void nrerror(char error_text[]);
	float gamser,gammcf,gln;

	if (x < 0.0 || a <= 0.0) nrerror("Invalid arguments in routine gammq");
	if (x < (a+1.0)) {
		gser(&gamser,a,x,&gln);
		return 1.0-gamser;
	} else {
		gcf(&gammcf,a,x,&gln);
		return gammcf;
	}
}


#define ITMAX 100
#define EPS 3.0e-7
#define FPMIN 1.0e-30

void gcf(float *gammcf, float a, float x, float *gln)
{
	float gammln(float xx);
	void nrerror(char error_text[]);
	int i;
	float an,b,c,d,del,h;

	*gln=gammln(a);
	b=x+1.0-a;
	c=1.0/FPMIN;
	d=1.0/b;
	h=d;
	for (i=1;i<=ITMAX;i++) {
		an = -i*(i-a);
		b += 2.0;
		d=an*d+b;
		if (fabs(d) < FPMIN) d=FPMIN;
		c=b+an/c;
		if (fabs(c) < FPMIN) c=FPMIN;
		d=1.0/d;
		del=d*c;
		h *= del;
		if (fabs(del-1.0) < EPS) break;
	}
	/*if (i > ITMAX) nrerror("a too large, ITMAX too small in gcf");*/
	*gammcf=exp(-x+a*log(x)-(*gln))*h;
}
#undef ITMAX
#undef EPS
#undef FPMIN


#define ITMAX 100
#define EPS 3.0e-7

void gser(float *gamser, float a, float x, float *gln)
{
	float gammln(float xx);
	void nrerror(char error_text[]);
	int n;
	float sum,del,ap;

	*gln=gammln(a);
	if (x <= 0.0) {
		if (x < 0.0) nrerror("x less than 0 in routine gser");
		*gamser=0.0;
		return;
	} else {
		ap=a;
		del=sum=1.0/a;
		for (n=1;n<=ITMAX;n++) {
			++ap;
			del *= x/ap;
			sum += del;
			if (fabs(del) < fabs(sum)*EPS) {
				*gamser=sum*exp(-x+a*log(x)-(*gln));
				return;
			}
		}
		nrerror("a too large, ITMAX too small in routine gser");
		return;
	}
}
#undef ITMAX
#undef EPS


float gammln(float xx)
{
	double x,y,tmp,ser;
	static double cof[6]={76.18009172947146,-86.50532032941677,
		24.01409824083091,-1.231739572450155,
		0.1208650973866179e-2,-0.5395239384953e-5};
	int j;

	y=x=xx;
	tmp=x+5.5;
	tmp -= (x+0.5)*log(tmp);
	ser=1.000000000190015;
	for (j=0;j<=5;j++) ser += cof[j]/++y;
	return -tmp+log(2.5066282746310005*ser/x);
}
