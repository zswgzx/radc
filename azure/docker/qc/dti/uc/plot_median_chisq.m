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

axis tight
xlabel('subjects');
ylabel('chisq value');
title('median chi-square value in brain tissue across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',10:10:nSubject);
%{
h=line([243.5 243.5],[-5 18]);               % define line object for display, change y range as needed
set(h,'LineStyle','--','Color','r');
h1=line([196.5 196.5],[-5 18]);
set(h1,'LineStyle','--','Color','r');
%}
set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','medianChiSq') % save figure as tiff, use screen resolution

system('mv medianChiSq.tif 150908');
cd ../outlier
end