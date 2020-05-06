function idx = plotChi2stats(filename)

%% Initialize variables.
if ~nargin, filename = 'subjsAll';end
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
thr=0.0265;
meanChisq=load('nonzero-meanchi2');
idx=find(meanChisq > thr);

n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

plot(1:nSubject,meanChisq,'.',1:nSubject,thr*ones(nSubject,1),'r--');

axis tight
xlabel('subjects');
ylabel('chisq value');
title('mean chi-square value in brain tissue across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','nonzero-meanchi2') % save figure as tiff, use screen resolution

end
