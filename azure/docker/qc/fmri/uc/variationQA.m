function idxs = variationQA()
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
meanD=zeros(1,nSubject);maxD=meanD;idxs=cell(1,2);
for i=1:nSubject
    curFld=pwd;
    file=sprintf('%s/data/mean/%s',curFld,subjects{i});
    meanD(i)=dlmread(file);
    file=sprintf('%s/data/max/%s',curFld,subjects{i});
    maxD(i)=dlmread(file);
end

thresholds={[0.8 0.9], 10}; % thresholds for mean and max per-slice variation in order

n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

% plot figures below
for i=1:2
    if (i<=1)
        plotData=meanD;
    else
        plotData=maxD;
    end
    
    figure;plot(1:nSubject,plotData,'.');

    xlabel('subjects');
    ylabel('Per slice variation');
    switch i
        case 1
            %meanOutlier=plotData;
            thrshld=thresholds{i};thrshld=thrshld';
            idx=find(plotData > thrshld(2) | plotData < thrshld(1) );     % find subjects out of range
            idxs{1,i}=idx;      % record subjects out of range
            thrshld=repmat(thrshld,1,nSubject);   % identify threshold for plot
            %hold on;plot(1:nSubject,thrshld(1,:),'r--',1:nSubject,thrshld(2,:),'r--',idx,plotData(idx),'ro');hold off   % highlight values out of range
            hold on;plot(1:nSubject,thrshld(1,:),'r--',1:nSubject,thrshld(2,:),'r--');   % highlight thresholds
            plot(hilight,plotData(hilight),'ro');hold off   % highlight subjects that fail displacement QA
            
            title('Mean per slice variation across subjects (subjects that fail displacement QA are circled in red)');
            filename='mean';
        case 2
            %maxOutlier=plotData;
            idx=find(plotData > thresholds{i});     % find subjects above threshold
            idxs{1,i}=idx;      % record subjects above threshold
            thrshld=repmat(thresholds{i},1,nSubject);   % identify threshold for plot
            %hold on;plot(1:nSubject,thrshld,'r--',idx,plotData(idx),'ro');hold off   % highlight values above threshold
            hold on;plot(1:nSubject,thrshld,'r--',hilight,plotData(hilight),'ro');hold off   % highlight subjects that fail displacement QA
            
            title('Max. per slice variation across subjects (subjects that fail displacement QA are circled in red)');
            filename='max';
    end
    axis tight
    
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);
    
    % save as tiff in max window size
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1])
    print('-dtiff','-r0',filename);
end

%[b,idx]=sort(data,'descend');

end