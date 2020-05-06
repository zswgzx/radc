function idxs = displacementQAnew()
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
nSubject=size(subjects);nSubject=nSubject(1);
nTimeIntrvl=159;nDisplacement=6;idxs=cell(1,nDisplacement);
tpIntrvl=4;

data=zeros(nTimeIntrvl,nDisplacement,nSubject);
for i=1:nSubject
    curFld=pwd;
    file=sprintf('%s/data/4tpi/%s',curFld,subjects{i});
    data(:,:,i)=dlmread(file);
end

newdata=zeros(nTimeIntrvl-tpIntrvl+1,nDisplacement,nSubject);
for i=1:(nTimeIntrvl-tpIntrvl+1)
    newdata(i,:,:)=max(data(i:(i+tpIntrvl-1),:,:))-min(data(i:(i+tpIntrvl-1),:,:));
end
maxDisp=max(newdata);

thresholds=1.9*ones(1,6); % thresholds for roll, pitch, yaw, ds (dz), dl (dx), and dp (dy) in order

n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

% plot figures below
for i=1:nDisplacement
    plotData=reshape(maxDisp(1,i,:),1,nSubject);
    idx=find(plotData > thresholds(i));     % find subjects above threshold
    idxs{1,i}=idx;      % record subjects above threshold
    thrshld=repmat(thresholds(i),1,nSubject);   % identify threshold for plot
    
    figure;plot(1:nSubject,plotData,'.',1:nSubject,thrshld,'r--');
    hold on;plot(idx,plotData(idx),'ro');hold off   % highlight values above threshold
    axis tight
    xlabel('subjects');
    switch i
        case 1
            %maxAbsRoll=plotData;
            ylabel('roll - range (degree)');
            title('displacement: max. range of roll across subjects in each 4 TR intervals');
            filename='roll';
        case 2
            %maxAbsPitch=plotData;
            ylabel('pitch - range (degree)');
            title('displacement: max. range of pitch across subjects in each 4 TR intervals');
            filename='pitch';
        case 3
            %maxAbsYaw=plotData;
            ylabel('yaw - range (degree)');
            title('displacement: max. range of yaw across subjects in each 4 TR intervals');
            filename='yaw';
        case 4
            %maxAbsDs=plotData;
            ylabel('Z displacement - range (mm)');
            title('displacement: max. range of displacement in Z direction across subjects in each 4 TR intervals');
            filename='z';
        case 5
            %maxAbsDl=plotData;
            ylabel('X displacement - range (mm)');
            title('displacement: max. range of displacement in X direction across subjects in each 4 TR intervals');
            filename='x';
        case 6
            %maxAbsDp=plotData;
            ylabel('Y displacement - range (mm)');
            title('displacement: max. range of displacement in Y direction across subjects in each 4 TR intervals');
            filename='y';
        otherwise
            disp('error');
    end
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);
    
    % save as tiff in max window size
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1])
    print('-dtiff','-r0',filename);
end

end