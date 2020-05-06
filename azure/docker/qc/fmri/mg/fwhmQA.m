function idxs = fwhmQA()
%% import subject names
filename = '/home/shengwei/work/QA/fmri/mg/150715/subjs';
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
dircFWHM=['x';'y';'z'];nTimePts=160;idxs=cell(1,6);

data=zeros(nTimePts,nSubject,length(dircFWHM));
for i=1:nSubject
    curFld=pwd;
    for j=1:length(dircFWHM)
        file=sprintf('%s/data/%s/%s',curFld,dircFWHM(j),subjects{i});
        data(:,i,j)=dlmread(file);
    end
end

meanD=mean(data);
maxD=max(data);

% plot figures below
stdRange=5;thr=5;
upperR=zeros(stdRange,nSubject);lowerR=upperR;
threshold=zeros(thr,nSubject);

n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

for i=1:6
    if (i<=3)
        plotData=meanD(1,:,i);
    else
        plotData=maxD(1,:,i-3);
    end
    
    meanR=repmat(mean(plotData),1,nSubject);
    stdR=repmat(std(plotData),1,nSubject);
    
    for j=1:stdRange
        upperR(j,:)=meanR+j*stdR;
        lowerR(j,:)=meanR-j*stdR;
        if j==thr
           threshold(1,:)=upperR(j,:);
           threshold(2,:)=lowerR(j,:);
        end
    end
    
    idx=find( (plotData > (mean(plotData)+thr*std(plotData))) | (plotData < (mean(plotData)-thr*std(plotData))));     % find subjects out of range
    idxs{1,i}=idx;      % record subjects out of range
    
    figure;plot(1:nSubject,plotData,'.',1:nSubject,meanR,'g--');
    hold on;
    for j=1:stdRange
        plot(1:nSubject,upperR(j,:),'r--',1:nSubject,lowerR(j,:),'r--');
    end
    plot(1:nSubject,threshold(1,:),'r',1:nSubject,threshold(2,:),'r'); % highlight threshold
    %plot(idx,plotData(idx),'ro');hold off   % highlight values out of range
    hold on;plot(hilight,plotData(hilight),'ro');hold off   % highlight subjects that fail displacement QA
    axis tight
    xlabel('subjects');
    ylabel('FWHM (mm? not sure)');
    switch i
        case 1
            %meanFwhmX=plotData;
            title('Mean FWHM in X direction across subjects');
            filename='mean-x';
        case 2
            %meanFwhmY=plotData;
            title('Mean FWHM in Y direction across subjects');
            filename='mean-y';
        case 3
            %meanFwhmZ=plotData;
            title('Mean FWHM in Z direction across subjects');
            filename='mean-z';
        case 4
            %maxFwhmX=plotData;
            title('Max. FWHM in X direction across subjects');
            filename='max-x';
        case 5
            %maxFwhmY=plotData;
            title('Max. FWHM in Y direction across subjects');
            filename='max-y';
        case 6
            %maxFwhmZ=plotData;
            title('Max. FWHM in Z direction across subjects');
            filename='max-z';
    end
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);
    
    % save as tiff in max window size
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1])
    print('-dtiff','-r0',filename);
end

%[b,idx]=sort(data,'descend');

%save('displacements.mat','subjects','data','maxAbsRoll','maxAbsPitch','maxAbsYaw','maxAbsDs','maxAbsDl','maxAbsDp');

end
