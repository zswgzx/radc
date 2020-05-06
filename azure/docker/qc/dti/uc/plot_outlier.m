function [] = plot_outlier()
    MedianOutlierPercent=dlmread('medianOutlier.txt');
    meanval=mean(MedianOutlierPercent);
    stdval=std(MedianOutlierPercent);
    nSubject=length(MedianOutlierPercent);
    
    Upper1=repmat(meanval+stdval,nSubject,1);
    Upper2=repmat(meanval+2*stdval,nSubject,1);
    Upper3=repmat(meanval+3*stdval,nSubject,1);
    Mean=repmat(meanval,nSubject,1);

    %save('medians.mat','MedianOutlierPercent','meanval','stdval')
    plot(1:nSubject,MedianOutlierPercent,'.',1:nSubject,Mean,'g--',...
    1:nSubject,Upper1,'r--',1:nSubject,Upper2,'r--',1:nSubject,Upper3,'r--');
    axis tight
    xlabel('subjects');
    ylabel('outlier percentage');
    title('median outlier percentage value in brain tissue across subjects');
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',10:10:nSubject);
    %{
    h=line([243.5 243.5],[5 45]);               % define line object for display, change y range as needed
    set(h,'LineStyle','--','Color','r');
    h1=line([196.5 196.5],[5 45]);
    set(h1,'LineStyle','--','Color','r');
    %}
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
    print('-dtiff','-r0','medianOutlier') % save figure as tiff, use screen resolution
    
    MeanOutlierPercent=dlmread('meanOutlier.txt');
    meanval=mean(MeanOutlierPercent);
    stdval=std(MeanOutlierPercent);
    nSubject=length(MeanOutlierPercent);
    
    Upper1=repmat(meanval+stdval,nSubject,1);
    Upper2=repmat(meanval+2*stdval,nSubject,1);
    Upper3=repmat(meanval+3*stdval,nSubject,1);
    Mean=repmat(meanval,nSubject,1);

    %save('means.mat','MeanOutlierPercent','meanval','stdval')
    figure
    plot(1:nSubject,MeanOutlierPercent,'.',1:nSubject,Mean,'g--',...
    1:nSubject,Upper1,'r--',1:nSubject,Upper2,'r--',1:nSubject,Upper3,'r--');
    axis tight
    xlabel('subjects');
    ylabel('outlier percentage');
    title('mean outlier percentage value in brain tissue across subjects');
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',10:10:nSubject);
    %{
    h=line([243.5 243.5],[5 45]);               % define line object for display, change y range as needed
    set(h,'LineStyle','--','Color','r');
    h1=line([196.5 196.5],[5 45]);
    set(h1,'LineStyle','--','Color','r');
    %}
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
    print('-dtiff','-r0','meanOutlier') % save figure as tiff, use screen resolution
    
    system('mv *.tif 150908');
    cd ../motion;
end