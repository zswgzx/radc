function [] = get_max_motion_alldirections()
%% Initialize variables.
filename = '../../subjects-all';
delimiter = '';

%% Format string for each line of text:
%   column1: text (%s)
% For more information, see the TEXTSCAN documentation.
formatSpec = '%s%[^\n\r]';

%% Open the text file.
fileID = fopen(filename,'r');

%% Read columns of data according to format string.
% This call is based on the structure of the file used to generate this
% code. If an error occurs for a different file, try regenerating the code
% from the Import Tool.
dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter,  'ReturnOnError', false);

%% Close the text file.
fclose(fileID);

%% Allocate imported array to column variable names
subjects = dataArray{:, 1};

%% Clear temporary variables
clearvars filename delimiter formatSpec fileID dataArray ans;
    
%% main
nSubject=size(subjects);nSubject=nSubject(1);

maxInterlaceAngle=zeros(nSubject,3);
maxInterlaceTrans=zeros(nSubject,3);

for i=1:nSubject
   filename=sprintf('%s-motion.mat',subjects{i});
   load(filename)
   
   maxInterlaceAngle(i,:)=max(abs(interlaceAngle));
   maxInterlaceTrans(i,:)=max(abs(interlaceTrans));
end

save('max-motion-alldir.mat','maxInterlaceAngle','maxInterlaceTrans')

%%
n50=floor(nSubject/50);
xticks=50*(1:n50);
xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
for i=1:n50
    xticklabs{5*i}=num2str(xticks(i));
end

plot(maxInterlaceAngle(:,1),'.')
axis tight
xlabel('subjects');
ylabel('degree');
title('Interlace-wise blind artifact check: max. Angle X of all gradients across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','interlace-maxAngleX') % save figure as tiff, use screen resolution
%close%{
%}
%%
figure;
plot(maxInterlaceAngle(:,2),'.')
axis tight
xlabel('subjects');
ylabel('degree');
title('Interlace-wise blind artifact check: max. Angle Y of all gradients across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','interlace-maxAngleY') % save figure as tiff, use screen resolution
%close%{
%}
%%
figure;
plot(maxInterlaceAngle(:,3),'.')
axis tight
xlabel('subjects');
ylabel('degree');
title('Interlace-wise blind artifact check: max. Angle Z of all gradients across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','interlace-maxAngleZ') % save figure as tiff, use screen resolution
%close%{
%}
%%
figure;
plot(maxInterlaceTrans(:,1),'.')
axis tight
xlabel('subjects');
ylabel('mm');
title('Interlace-wise blind artifact check: max. Translation X of all gradients across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','interlace-maxTransX') % save figure as tiff, use screen resolution
%close%{
%}
%%
figure;
plot(maxInterlaceTrans(:,2),'.')
axis tight
xlabel('subjects');
ylabel('mm');
title('Interlace-wise blind artifact check: max. Translation Y of all gradients across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','interlace-maxTransY') % save figure as tiff, use screen resolution
%close%{
%}
%%
figure;
plot(maxInterlaceTrans(:,3),'.')
axis tight
xlabel('subjects');
ylabel('mm');
title('Interlace-wise blind artifact check: max. Translation Z of all gradients across subjects');
set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
print('-dtiff','-r0','interlace-maxTransZ') % save figure as tiff, use screen resolution
%close%{
%}
system('mv [12]*.mat mats');
cd ../../snr
end
