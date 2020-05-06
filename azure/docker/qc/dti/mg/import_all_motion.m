function [] = import_all_motion()
    %% Initialize variables.
    filename = '../subjects-all';
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
    nSubject=length(subjects);
    maxAngle=zeros(nSubject,3);
    maxTrans=zeros(nSubject,3);

    for i=1:nSubject
        %{
        file=sprintf('%s-motion',subjects{i});
        [rot,trans]=importMotion(file);
        file=sprintf('%s-motion.mat',subjects{i});
        save(file,'rot','trans');
        %}
        file=sprintf('%s-motion.mat',subjects{i});
        load(file);
        
        maxAngle(i,:)=max(abs(rot));
        maxTrans(i,:)=max(abs(trans));
    end
    
    save('max-motion-alldir.mat','maxAngle','maxTrans')
    
    %% plot figures
    n50=floor(nSubject/50);
    xticks=50*(1:n50);
    xticklabs=cell(1,n50*5+floor(mod(nSubject,50)/10));
    for i=1:n50
        xticklabs{5*i}=num2str(xticks(i));
    end
    
    plot(maxAngle(:,1),'.')
    axis tight
    xlabel('subjects');
    ylabel('radian');
    title('TORTOISE-corrected DWs motion artifact check: max. abs. Angle X of all gradients across subjects');
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);
    
    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
    print('-dtiff','-r0','maxAngleX') % save figure as tiff, use screen resolution
    %close
    %%
    plot(maxAngle(:,2),'.')
    axis tight
    xlabel('subjects');
    ylabel('radian');
    title('TORTOISE-corrected DWs motion artifact check: max. abs. Angle Y of all gradients across subjects');
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
    print('-dtiff','-r0','maxAngleY') % save figure as tiff, use screen resolution
    %close
    %%
    plot(maxAngle(:,3),'.')
    axis tight
    xlabel('subjects');
    ylabel('radian');
    title('TORTOISE-corrected DWs motion artifact check: max. abs. Angle Z of all gradients across subjects');
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
    print('-dtiff','-r0','maxAngleZ') % save figure as tiff, use screen resolution
    %close

    %%
    plot(maxTrans(:,1),'.')
    axis tight
    xlabel('subjects');
    ylabel('mm');
    title('TORTOISE-corrected DWs motion artifact check: max. abs. Translation X of all gradients across subjects');
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
    print('-dtiff','-r0','maxTransX') % save figure as tiff, use screen resolution
    %close
    %%
    plot(maxTrans(:,2),'.')
    axis tight
    xlabel('subjects');
    ylabel('mm');
    title('TORTOISE-corrected DWs motion artifact check: max. abs. Translation Y of all gradients across subjects');
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
    print('-dtiff','-r0','maxTransY') % save figure as tiff, use screen resolution
    %close
    %%
    plot(maxTrans(:,3),'.')
    axis tight
    xlabel('subjects');
    ylabel('mm');
    title('TORTOISE-corrected DWs motion artifact check: max. abs. Translation Z of all gradients across subjects');
    set(gca,'XGrid','on','XTick',10:10:nSubject,'XTickLabel',xticklabs);

    set(gcf,'PaperPositionMode','auto','units','normalized','outerposition',[0 0 1 1]) % preserve the image aspect ratio when printing, maximize figure window
    print('-dtiff','-r0','maxTransZ') % save figure as tiff, use screen resolution
    %close
    
    system('mv [12]*.mat mats;mv *.tif max*.mat results'); 
end

function [rot,trans] = importMotion(filename, startRow, endRow)
    %IMPORTFILE Import numeric data from a text file as column vectors.
    %   [VARNAME1,VARNAME2,VARNAME3,VARNAME5,VARNAME6,VARNAME7] =
    %   IMPORTFILE(FILENAME) Reads data from text file FILENAME for the default
    %   selection.
    %
    %   [VARNAME1,VARNAME2,VARNAME3,VARNAME5,VARNAME6,VARNAME7] =
    %   IMPORTFILE(FILENAME, STARTROW, ENDROW) Reads data from rows STARTROW
    %   through ENDROW of text file FILENAME.
    %
    % Example:
    %   [VarName1,VarName2,VarName3,VarName5,VarName6,VarName7] =
    %   importfile('motion',1, 84);
    %
    %    See also TEXTSCAN.

    % Auto-generated by MATLAB on 2013/11/04 15:34:18

    %% Initialize variables.
    delimiter = {'\t',' '};
    if nargin<=2
        startRow = 1;
        endRow = inf;
    end

    %% Format string for each line of text:
    %   column1-7: double (%f)
    % For more information, see the TEXTSCAN documentation.
    formatSpec = '%f%f%f%*s%f%f%f%[^\n\r]';

    %% Open the text file.
    fileID = fopen(filename,'r');

    %% Read columns of data according to format string.
    % This call is based on the structure of the file used to generate this
    % code. If an error occurs for a different file, try regenerating the code
    % from the Import Tool.
    dataArray = textscan(fileID, formatSpec, endRow(1)-startRow(1)+1, 'Delimiter', delimiter, 'HeaderLines', startRow(1)-1, 'ReturnOnError', false);
    for block=2:length(startRow)
        frewind(fileID);
        dataArrayBlock = textscan(fileID, formatSpec, endRow(block)-startRow(block)+1, 'Delimiter', delimiter, 'HeaderLines', startRow(block)-1, 'ReturnOnError', false);
        for col=1:length(dataArray)
            dataArray{col} = [dataArray{col};dataArrayBlock{col}];
        end
    end

    %% Close the text file.
    fclose(fileID);

    %% Allocate imported array to column variable names
    rot = [dataArray{:, 1} dataArray{:, 2} dataArray{:, 3}];
    trans = [dataArray{:, 4} dataArray{:, 5} dataArray{:, 6}];
end
