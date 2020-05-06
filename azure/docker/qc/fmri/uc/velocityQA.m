function idxs = velocityQA()
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
nTimePts=160;
maskedD=zeros(nTimePts,nSubject);idxs=cell(1,2); %unmaskedD=maskedD;
for i=1:nSubject
    curFld=pwd;
    file=sprintf('%s/data/masked/%s',curFld,subjects{i});
    maskedD(:,i)=dlmread(file);
    %file=sprintf('%s/data/unmasked/%s',curFld,subjects{i});
    %unmaskedD(:,i)=dlmread(file);
end

meanMaskedD=repmat(mean(maskedD),nTimePts,1);
%meanUnmaskedD=repmat(mean(unmaskedD),nTimePts,1);

maxAbsVlcMasked=100*max(abs(diff(maskedD./meanMaskedD)));
%maxAbsVlcUnmasked=100*max(abs(diff(unmaskedD./meanUnmaskedD)));
meanAbsVlcMasked=100*mean(abs(diff(maskedD./meanMaskedD)));
%meanAbsVlcUnmasked=100*mean(abs(diff(unmaskedD./meanUnmaskedD)));

thresholds=[4 1]; % thresholds for masked and unmasked velocity in order

n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

% plot figures below
for i=1:2
    switch i
        case 1
            plotData=maxAbsVlcMasked;
        case 2
            plotData=meanAbsVlcMasked;
            %{
        case 2
            plotData=maxAbsVlcUnmasked;
        case 3
            plotData=meanAbsVlcMasked;
        case 4
            plotData=meanAbsVlcUnmasked;
            %}
    end
    idx=find(plotData > thresholds(i));     % find subjects above threshold
    idxs{1,i}=idx;      % record subjects above threshold
    thrshld=repmat(thresholds(i),1,nSubject);   % identify threshold for plot
    
    figure;plot(1:nSubject,plotData,'.',1:nSubject,thrshld,'r--');
    %hold on;plot(idx,plotData(idx),'ro');hold off   % highlight values above threshold
    hold on;plot(hilight,plotData(hilight),'ro');hold off   % highlight subjects that fail displacement QA
    axis tight
    xlabel('subjects');
    ylabel('Percentage (%)');
    switch i
        case 1
            %meanOutlier=plotData;
            title('Max. abs. velocity of masked volmean across subjects (subjects that fail displacement QA are circled in red)');
            filename='max-4pct';
        case 2
            title('Mean. abs. velocity of masked volmean across subjects (subjects that fail displacement QA are circled in red)');
            filename='mean-1pct';
            %{
        case 2
            %maxOutlier=plotData;
            title('Max. abs. velocity of unmasked volmean across subjects');
        case 3
            title('Mean. abs. velocity of masked volmean across subjects');
        case 4
            title('Mean. abs. velocity of unmasked volmean across subjects');
            %}
    end
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);
    
    % save as tiff in max window size
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1])
    print('-dtiff','-r0',filename);
end

%[b,idx]=sort(data,'descend');

end