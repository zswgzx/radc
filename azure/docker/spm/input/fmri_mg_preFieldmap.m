function fmri_mg_postFieldmap(fn,ord)
% fn: a 4D nifti file containing the resting state scans
% ord(optional): specify the processes to run
%
% Written by Aaron Schultz, May 5th, 2010 (aschultz@martinos.org)
% Last Updated Dec. 11 2012;

% include the full path for input variable fn
% e.g. to run all steps, do Preproc_rfMRI('path/to/rfmri.nii');
%      to run some step(s), do Preproc_rfMRI('path/to/rfmri.nii',1(or 2));
% this is for preprocessing before fieldmap distortion correction.
% Shengwei last updated

if nargin == 0 || isempty(fn);
    error('Need at least one input argument.');
end

% check if fn exists
[fnPathstr,~,~] = fileparts(fn);
if ~exist(fn,'file')  
    error('Input nii file does not exist.');
end

pname = 'mg_preFieldmap';
P = mg_preFieldmap;

% check if ord exists
if nargin<2
   ord = 1:length(P.PO); 
end

disp(['Running in ',fnPathstr]);
time=spm('time');
fprintf('Started at %s\n',time);

% main
nfn=fn;
for qq = 1:length(ord)
   eval(P.PO{ord(qq)});
end

time=spm('time');
fprintf('\nFinished at %s\n',time);

if ~exist([fnPathstr,'/', pname '.mat'],'file')
    save([fnPathstr,'/', pname '.mat'],'P');
end

function nfn = slice_time(fn)
    [~,fnName,fnExt] = fileparts(fn);
    fprintf('\n====================\nPERFORMING SLICE TIME CORRECTION:\n');
    if P.st.do
        spm_slice_timing(fn, P.st.sliceorder, P.st.refslice, P.st.timing, P.st.prefix);
        nfn = [fnPathstr,'/',P.st.prefix,fnName,fnExt];
        P.st.UserTime = UserTime;
    else
        fprintf('\nSKIPPING SLICE TIMING\n');
        nfn = fn;
    end
    spm_figure('Close');
end

function nfn = realign(fn)
    [~,fnName,fnExt] = fileparts(fn);
    fprintf('\n====================\nREALIGNING IMAGES:\n');
    if P.rr.do
        spm_realign(fn,P.rr.RealignPars);
        spm_reslice(fn,P.rr.ReslicePars);
        nfn = [fnPathstr,'/',P.rr.ReslicePars.prefix,fnName,fnExt];
        P.rr.UserTime = UserTime;
    else
        fprintf('\nSKIPPING REALIGNMENT\n');
        nfn = fn;
    end
end

function out = UserTime
    tmp = pwd;
    cd ~
    user = pwd;
    cd(tmp);
        
    ind = find(user == filesep);
    if ind(end)==numel(user);
        user = user(ind(end-1)+1:ind(end)-1);
    else
        user = user(ind(end)+1:end);
    end
    out = ['last run by ' user ' on ' datestr(clock)];
end

function P = mg_preFieldmap
    nslices=38;
    dropvols=0;
    TR=3;                                                      % secs

    P.PO = [];                                                 % Specify which Steps to run and in which order
    P.PO{1} = 'nfn = slice_time(nfn);';
    P.PO{2} = 'nfn = realign(nfn);';

    P.TR    = TR;                                              % Specify TR here
    %%
    P.st.do                 = true;
    %P.st.sliceorder         = [1:2:nslices,2:2:nslices];       % slice acquisition order before 150715
    P.st.sliceorder         = [1:nslices];                     % slice acquisition order
    P.st.refslice           = floor(nslices/2);                % Reference slice (1=bottom)
    realTR                  = P.TR/nslices;
    P.st.timing             = [realTR realTR-realTR/nslices];  % sequence timing, [time between slices time between last slices and next volume]
    P.st.prefix             = 'st_';

    P.rr.do                 = true;
    % Realign:
    P.rr.RealignPars.quality= .9;                              % Quality versus speed trade-off
    P.rr.RealignPars.fwhm   = 5;                               % pre alignment Guassian smoothing kernel in mm
    P.rr.RealignPars.sep    = 2;                               % The separation (in mm) between the points sampled in the reference image. The smaller, the slower.
    %P.rr.RealignPars.rtm    = 0;                               % Register to mean ? ("MRI images are typically registered to first")
    %P.rr.RealignPars.PW     = '';                              % no weigthing image
    P.rr.RealignPars.interp = 2;                               % order of interpolation function for resampling
    P.rr.RealignPars.wrap   = [0 0 0];                         % No wrapping

    % Reslice:
    P.rr.ReslicePars.mask   = 1;                               % mask images: if one timepoint in a voxel is 0, all timepoints in that voxel are set to 0
    P.rr.ReslicePars.mean   = 1;                               % Write a Mean image
    P.rr.ReslicePars.interp = 4;                               % interpolation order for resampling
    P.rr.ReslicePars.which  = 2;                               % Reslice all images including the first one  
    P.rr.ReslicePars.warp   = [0 0 0];                         % No wrapping
    P.rr.ReslicePars.prefix = 'rr_';
end
end
