function [] = import_new_snr()

    %% Initialize variables.
    filename = '../dtiprep/subjects';
    delimiter = '';

    %% Format string for each line of text:
    formatSpec = '%s%[^\n\r]';

    %% Open the text file.
    fileID = fopen(filename,'r');

    %% Read columns of data according to format string.
    dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter,  'ReturnOnError', false);

    %% Close the text file.
    fclose(fileID);
    %% Allocate imported array to column variable names
    subjects = dataArray{:, 1};

    %% Clear temporary variables
    clearvars filename delimiter formatSpec fileID dataArray ans;

    %% main
    nSubject=length(subjects);

    for i=1:nSubject
        file=sprintf('%s-snr',subjects{i});
        snr=ImportSNR(file);
        file=sprintf('%s-QA-data.mat',subjects{i});
        save(file,'snr');
    end
    
    system('mv *s{td,nr} stats/150908;mv matlab/*.mat .');
end

function SNR = ImportSNR(filename, startRow, endRow)
    %IMPORTFILE Import numeric data from a text file as column vectors.
    %   [VOL,SNR] = IMPORTFILE(FILENAME) Reads data from text file FILENAME for
    %   the default selection.
    %
    %   [VOL,SNR] = IMPORTFILE(FILENAME, STARTROW, ENDROW) Reads data from rows
    %   STARTROW through ENDROW of text file FILENAME.
    %
    % Example:
    %   [vol,SNR] = importfile('snr',1, 84);

    %% Initialize variables.
    delimiter = '\t';
    if nargin<=2
        startRow = 1;
        endRow = inf;
    end

    %% Format string for each line of text:
    %   column1: text (%s)
    %	column2: double (%f)
    % For more information, see the TEXTSCAN documentation.
    formatSpec = '%s%f%[^\n\r]';

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
    SNR = dataArray{:,2};
end
