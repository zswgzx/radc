function [] = get_snr_stats()

%% Initialize variables.
filename = '../subjects-all';
delimiter = '';

%% Format string for each line of text:
formatSpec = '%s%[^\n\r]';

%% Open the text file.
fileID = fopen(filename,'r');

%% Read columns of data according to format string.
dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter,  'ReturnOnError', false);

%% Close the text file.
fclose(fileID);
%% Allocate imported array to column variable names
subjects = dataArray{:, 1};

%% Clear temporary variables
clearvars filename delimiter formatSpec fileID dataArray ans;

%% main
nSubject=length(subjects);
nDWDirection=41;
nB0=1;

SNRs=zeros(nSubject,nDWDirection);

for i=1:nSubject
   filename=sprintf('%s-QA-data',subjects{i});
   load(filename,'snr');
   SNRs(i,:)=snr;  
end

% SNR_B0s=(SNRs(:,1:nB0))';
% stdB0SNRs=std(SNR_B0s);
% meanStdB0SNRs=repmat(mean(stdB0SNRs),1,nSubject);
% stdUpper1=repmat(mean(stdB0SNRs)+std(stdB0SNRs),1,nSubject);
% stdUpper2=repmat(mean(stdB0SNRs)+2*std(stdB0SNRs),1,nSubject);
% stdUpper3=repmat(mean(stdB0SNRs)+3*std(stdB0SNRs),1,nSubject);

meanSNRsLine=mean(SNRs);
stdSNRsLine=std(SNRs);

meanUpper1=meanSNRsLine+stdSNRsLine;
meanUpper2=meanSNRsLine+2*stdSNRsLine;
meanUpper3=meanSNRsLine+3*stdSNRsLine;
meanLower1=meanSNRsLine-stdSNRsLine;
meanLower2=meanSNRsLine-2*stdSNRsLine;
meanLower3=meanSNRsLine-3*stdSNRsLine;

meanSNRsLine=repmat(meanSNRsLine,nSubject,1);
meanUpper1=repmat(meanUpper1,nSubject,1);
meanUpper2=repmat(meanUpper2,nSubject,1);
meanUpper3=repmat(meanUpper3,nSubject,1);
meanLower1=repmat(meanLower1,nSubject,1);
meanLower2=repmat(meanLower2,nSubject,1);
meanLower3=repmat(meanLower3,nSubject,1);

save('snr-allstat.mat','nSubject','nDWDirection','meanSNRsLine','SNRs','subjects',...
    'meanUpper1','meanUpper2','meanUpper3','meanLower1','meanLower2','meanLower3','nB0')%,'stdB0SNRs'

% plot std of 6 SNRs for B0s across subjects
% plot(1:nSubject,stdB0SNRs,'.',1:nSubject,meanStdB0SNRs,'g--',...
%     1:nSubject,stdUpper1,'r--',1:nSubject,stdUpper2,'r--',1:nSubject,stdUpper3,'r--');
% axis tight
% xlabel('subjects');
% ylabel('standard deviation of 6 SNRs from B0 volumes');
% title('standard deviation of 6 SNRs from B0 volumes across subjects');
% set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',10:10:nSubject);
% 
% set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
% print('-dtiff','-r0','std-b0SNRs') % save figure as tiff, use screen resolution
% close

% plot mean of SNRs for B0s & DWs across subjects
for col=1:nB0
    plot(1:nSubject,SNRs(:,col),'.',1:nSubject,meanSNRsLine(:,col),'g--',...
        1:nSubject,meanUpper1(:,col),'r--',1:nSubject,meanUpper2(:,col),'r--',1:nSubject,meanUpper3(:,col),'r--',...
        1:nSubject,meanLower1(:,col),'r--',1:nSubject,meanLower2(:,col),'r--',1:nSubject,meanLower3(:,col),'r--');
    axis tight
    filename=sprintf('%02d',col-1);
    xlabel('subjects');
    ylabel(['SNR of B0\_',filename,' volumes']);
    title(['SNRs from B0\_',filename,' across subjects']);
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',10:10:nSubject);
    
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
    %{
    h=line([243.5 243.5],[-5 5]);               % define line object for display, change y range as needed
    set(h,'LineStyle','--','Color','r');
    h1=line([196.5 196.5],[-5 5]);
    set(h1,'LineStyle','--','Color','r');
    %}
    print('-dtiff','-r0',['mean-b0-',filename,'-SNRs']) % save figure as tiff, use screen resolution
    close
end

for col=(nB0+1):nDWDirection
    plot(1:nSubject,SNRs(:,col),'.',1:nSubject,meanSNRsLine(:,col),'g--',...
        1:nSubject,meanUpper1(:,col),'r--',1:nSubject,meanUpper2(:,col),'r--',1:nSubject,meanUpper3(:,col),'r--',...
        1:nSubject,meanLower1(:,col),'r--',1:nSubject,meanLower2(:,col),'r--',1:nSubject,meanLower3(:,col),'r--');
    axis tight
    xlabel('subjects');
    filename=sprintf('%02d',col-nB0-1);
    ylabel(['SNR of DW',filename,' volumes']);
    title(['SNRs from DW',filename,'s across subjects']);
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',10:10:nSubject);
    
    filename=['mean-dw',filename,'SNRs'];
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1])
    %{
    h=line([243.5 243.5],[-5 5]);               % define line object for display, change y range as needed
    set(h,'LineStyle','--','Color','r');
    h1=line([196.5 196.5],[-5 5]);
    set(h1,'LineStyle','--','Color','r');
    %}
    print('-dtiff','-r0',filename);
    % tb = axtoolbar('default');
    % tb.Visible = 'on';
    clf;
end

system('mv [12]*.mat matlab;mv *.tif snr-all* results/150908');
cd ../chisquare;
end
