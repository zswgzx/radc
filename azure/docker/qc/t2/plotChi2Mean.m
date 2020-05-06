function plotChi2Mean(filename)

%% Initialize variables.
if ~nargin, filename = '../subjects-all';end
delimiter = '';

%% Format string for each line of text:
%   column1: text (%s)
% For more information, see the TEXTSCAN documentation.
formatSpec = '%s%[^\n\r]';

%% Open the text file.
fileID = fopen(filename,'r');

%% Read columns of data according to format string.
% This call is based on the structure of the file used to generate this
% code. If an error occurs for a different file, try regenerating the code
% from the Import Tool.
dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter,  'ReturnOnError', false);

%% Close the text file.
fclose(fileID);

%% Allocate imported array to column variable names
subjects = dataArray{:, 1};

%% Clear temporary variables
clearvars filename delimiter formatSpec fileID dataArray ans;

%% main
nSubject=size(subjects);nSubject=nSubject(1);

meanChisq=load('nonzero-mean');
%medianChisq=load('nonzero-median');
%stdChisq=load('nonzero-std');

MeanOfMean=mean(meanChisq);
StdOfMean=std(meanChisq);
%{
MeanOfMedian=mean(medianChisq);
StdOfMedian=std(medianChisq);
MeanOfStd=mean(stdChisq);
StdOfStd=std(stdChisq);
%}
save('data.mat','subjects','meanChisq','MeanOfMean','StdOfMean','nSubject');

%%
Upper1=repmat(MeanOfMean+StdOfMean,nSubject,1);
Upper2=repmat(MeanOfMean+2*StdOfMean,nSubject,1);
Upper3=repmat(MeanOfMean+3*StdOfMean,nSubject,1);
Lower1=repmat(MeanOfMean-StdOfMean,nSubject,1);
Lower2=repmat(MeanOfMean-2*StdOfMean,nSubject,1);
Lower3=repmat(MeanOfMean-3*StdOfMean,nSubject,1);
Mean=repmat(MeanOfMean,nSubject,1);

plot(1:nSubject,meanChisq,'.',1:nSubject,Mean,'g',...
    1:nSubject,Upper1,'r',1:nSubject,Upper2,'r',1:nSubject,Upper3,'r',...
    1:nSubject,Lower1,'r',1:nSubject,Lower2,'r',1:nSubject,Lower3,'r');

n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

axis tight
xlabel('subjects');
ylabel('chisq value');
title('mean chi-square value in brain tissue across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','meanChi2') % save figure as tiff, use screen resolution
%{
Upper1=repmat(MeanOfMedian+StdOfMedian,nSubject,1);
Upper2=repmat(MeanOfMedian+2*StdOfMedian,nSubject,1);
Upper3=repmat(MeanOfMedian+3*StdOfMedian,nSubject,1);
Lower1=repmat(MeanOfMedian-StdOfMedian,nSubject,1);
Lower2=repmat(MeanOfMedian-2*StdOfMedian,nSubject,1);
Lower3=repmat(MeanOfMedian-3*StdOfMedian,nSubject,1);
Mean=repmat(MeanOfMedian,nSubject,1);

figure;
plot(1:nSubject,medianChisq,'*-',1:nSubject,Mean,'g',...
    1:nSubject,Upper1,'r',1:nSubject,Upper2,'r',1:nSubject,Upper3,'r',...
    1:nSubject,Lower1,'r',1:nSubject,Lower2,'r',1:nSubject,Lower3,'r');

axis tight
xlabel('subjects');
ylabel('chisq value');
title('median chi-square value in brain tissue across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',10:10:nSubject);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
%print('-dtiff','-r0','median-chisq') % save figure as tiff, use screen resolution

Upper1=repmat(MeanOfStd+StdOfStd,nSubject,1);
Upper2=repmat(MeanOfStd+2*StdOfStd,nSubject,1);
Upper3=repmat(MeanOfStd+3*StdOfStd,nSubject,1);
Lower1=repmat(MeanOfStd-StdOfStd,nSubject,1);
Lower2=repmat(MeanOfStd-2*StdOfStd,nSubject,1);
Lower3=repmat(MeanOfStd-3*StdOfStd,nSubject,1);
Mean=repmat(MeanOfStd,nSubject,1);

figure;
plot(1:nSubject,stdChisq,'*-',1:nSubject,Mean,'g',...
    1:nSubject,Upper1,'r',1:nSubject,Upper2,'r',1:nSubject,Upper3,'r',...
    1:nSubject,Lower1,'r',1:nSubject,Lower2,'r',1:nSubject,Lower3,'r');

axis tight
xlabel('subjects');
ylabel('chisq value');
title('Std chi-square value in brain tissue across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',10:10:nSubject);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
%print('-dtiff','-r0','std-chisq') % save figure as tiff, use screen resolution
%}
end
