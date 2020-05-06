function idxs = interleaveQA()
%% import subject names
filename = '/home/shengwei/work/QA/fmri/uc/150908/subjs';
delimiter = '';
formatSpec = '%s%[^\n\r]';
fileID = fopen(filename,'r');
dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter,  'ReturnOnError', false);
fclose(fileID);
subjects = dataArray{:, 1};
clearvars filename delimiter formatSpec fileID dataArray ans;

%% main

% load variable to highlight subjects that fail displacment QA step
load('../idx_exceed_thresholds.mat','displacement19');
hilight=displacement19;

nSubject=size(subjects);nSubject=nSubject(1);
nSlice=45;nTimePoint=160;
maskedD=zeros(nSlice,nTimePoint,nSubject);idxs=cell(1);

for i=1:nSubject
    curFld=pwd;
    file=sprintf('%s/data/%s',curFld,subjects{i});
    maskedD(:,:,i)=dlmread(file);
end
maskedStat=2*abs(diff(maskedD))./(maskedD(1:end-1,:,:)+maskedD(2:end,:,:));  % abs. of successive difference, normalized by their mean
maskedStat(maskedStat==2)=NaN;  % this excludes the case where one of successive slices has 0 mean value
meanMaskedStat=reshape(mean(nanmedian(maskedStat)),1,nSubject);
medianMaskedStat=reshape(max(nanmedian(maskedStat)),1,nSubject);
%[~,I]=max(nanmedian(maskedStat));  % track index of max for debuging

threshold=[0.035 0.06]; % thresholds for masked percentage difference in order

n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

% plot figures below
for i=1:2
    if (i<=1)
        plotData=meanMaskedStat;
    else
        plotData=medianMaskedStat;
    end
    idx=find(plotData > threshold(i));     % find subjects above threshold
    idxs{1,i}=idx;      % record subjects above threshold
    thrshld=repmat(threshold(i),1,nSubject);   % identify threshold for plot
    
    figure;plot(1:nSubject,plotData,'.',1:nSubject,thrshld,'r--');
    %hold on;plot(idx,plotData(idx),'ro');hold off   % highlight values above threshold
    hold on;plot(hilight,plotData(hilight),'ro');hold off   % highlight subjects that fail displacement QA
    
    axis tight
    xlabel('subjects');
    %ylabel('Percentage difference (%)');
    switch i
        case 1
            %meanOutlier=plotData;
            title('Mean median of masked interleave measure from first timepoint across subjects (subjects that fail displacement QA are circled in red)');
            filename='meanmedian';
        case 2
            %maxOutlier=plotData;
            title('Max median of masked interleave measure from first timepoint across subjects (subjects that fail displacement QA are circled in red)');
            filename='maxmedian';
    end
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);
    
    % save as tiff in max window size
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1])
    print('-dtiff','-r0',filename);
end

end