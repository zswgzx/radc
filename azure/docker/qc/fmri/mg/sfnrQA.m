function idx = sfnrQA()

% load variable to highlight subjects that fail displacment QA step
load('../idx_exceed_thresholds.mat','displacement19');
hilight=displacement19;

stdRange=3;thr=2;
data=dlmread('sfnrs');
nSubject=length(data);

meanD=mean(data)*ones(nSubject,1);
stdD=std(data)*ones(nSubject,1);
upperLim=zeros(nSubject,stdRange);lowerLim=upperLim;

for i=1:stdRange
    upperLim(:,i)=meanD+i*stdD;
    lowerLim(:,i)=meanD-i*stdD;
end
threshold=mean(data)-thr*std(data);


idx=find(data < threshold);     % find subjects below threshold
figure;
plot(1:nSubject,data,'.',1:nSubject,meanD,'g--');

hold on;
for i=1:stdRange
    plot(1:nSubject,upperLim(:,i),'r--',1:nSubject,lowerLim(:,i),'r--');
end

plot(1:nSubject,threshold,'r','LineWidth',10); % highlight threshold
%plot(idx,data(idx),'ro');hold off   % highlight values below threshold
plot(hilight,data(hilight),'ro');hold off   % highlight subjects that fail displacement QA

n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

axis tight
xlabel('subjects');
ylabel('SFNR');
title('whole brain SFNR across subjects (subjects that fail displacement QA are circled in red)');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

% save as tiff in max window size
set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1])
print('-dtiff','-r0','sfnr');
end
