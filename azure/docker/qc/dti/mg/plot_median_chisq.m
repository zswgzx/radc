function [] = plot_median_chisq()

data=dlmread('medianChisq.txt');
nSubject=length(data);
meanval=mean(data);
stdval=std(data);

Upper1=repmat(meanval+stdval,nSubject,1);
Upper2=repmat(meanval+2*stdval,nSubject,1);
Upper3=repmat(meanval+3*stdval,nSubject,1);
Lower1=repmat(meanval-stdval,nSubject,1);
Lower2=repmat(meanval-2*stdval,nSubject,1);
Lower3=repmat(meanval-3*stdval,nSubject,1);
Mean=repmat(meanval,nSubject,1);

plot(1:nSubject,data,'.',1:nSubject,Mean,'g--',...
    1:nSubject,Upper1,'r--',1:nSubject,Upper2,'r--',1:nSubject,Upper3,'r--',...
    1:nSubject,Lower1,'r--',1:nSubject,Lower2,'r--',1:nSubject,Lower3,'r--');

n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

axis tight
xlabel('subjects');
ylabel('chisq value');
title('median chi-square value in brain tissue across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','median-chisq') % save figure as tiff, use screen resolution
cd ../outlier
end