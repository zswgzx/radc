function [] = getNewXmlMotion()
    %% Initialize variables.
    filename = '../subjects';
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
    length=size(subjects);length=length(1);

    for i=1:length
       filename=sprintf('%s-dwi_XMLQCResult.xml',subjects{i});
       [interlaceAngle,interlaceTrans,~,~] = getXmlMotion(filename);
       filename=sprintf('%s-motion.mat',subjects{i});
       save(filename,'interlaceAngle','interlaceTrans')
    end
    
    system('mv [12]*.xml xmls;mv mats/[12]*.mat .');
end

function [interlaceAngle,interlaceTrans,gradientAngle,gradientTrans] = getXmlMotion(filename)

    % see http://blogs.mathworks.com/community/2010/11/01/xml-and-matlab-navigating-a-tree/

    gradMotion=xmlread(filename);

    % get the xpath mechanism into the workspace
    import javax.xml.xpath.*
    factory = XPathFactory.newInstance;
    xpath = factory.newXPath;

    numVol=46;
    interlaceAngle=zeros(numVol,3);
    interlaceTrans=zeros(numVol,3);
    gradientAngle=zeros(numVol,3);
    gradientTrans=zeros(numVol,3);

    for i=0:numVol-1
        gradient=sprintf('\''gradient_%04d\''',i);

        expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/processing'];
        expression = xpath.compile(expr);
        status=expression.evaluate(gradMotion,XPathConstants.STRING);

        if strcmp(status,'NA')
            interlaceAngle(i+1,:)=NaN(1,3);
            interlaceTrans(i+1,:)=NaN(1,3);
        else
            expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceAngleX'']/green'];
            expression = xpath.compile(expr);
            interlaceAngle(i+1,1)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
            if isnan(interlaceAngle(i+1,1))
                expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceAngleX'']/red'];
                expression = xpath.compile(expr);
                interlaceAngle(i+1,1)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
            end

            expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceAngleY'']/green'];
            expression = xpath.compile(expr);
            interlaceAngle(i+1,2)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
            if isnan(interlaceAngle(i+1,2))
                expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceAngleY'']/red'];
                expression = xpath.compile(expr);
                interlaceAngle(i+1,2)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
            end

            expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceAngleZ'']/green'];
            expression = xpath.compile(expr);
            interlaceAngle(i+1,3)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
            if isnan(interlaceAngle(i+1,3))
                expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceAngleZ'']/red'];
                expression = xpath.compile(expr);
                interlaceAngle(i+1,3)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
            end

            if (norm(interlaceAngle(i+1,:)+ones(1,3))<eps)
                interlaceAngle(i+1,:)=NaN(1,3);
                interlaceTrans(i+1,:)=NaN(1,3);
            else
                expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceTranslationX'']/green'];
                expression = xpath.compile(expr);
                interlaceTrans(i+1,1)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
                if isnan(interlaceTrans(i+1,1))
                    expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceTranslationX'']/red'];
                    expression = xpath.compile(expr);
                    interlaceTrans(i+1,1)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
                end

                expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceTranslationY'']/green'];
                expression = xpath.compile(expr);
                interlaceTrans(i+1,2)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
                if isnan(interlaceTrans(i+1,2))
                    expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceTranslationY'']/red'];
                    expression = xpath.compile(expr);
                    interlaceTrans(i+1,2)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
                end

                expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceTranslationZ'']/green'];
                expression = xpath.compile(expr);
                interlaceTrans(i+1,3)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
                if isnan(interlaceTrans(i+1,3))
                    expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''InterlaceWiseCheck'']/entry[@parameter=''InterlaceTranslationZ'']/red'];
                    expression = xpath.compile(expr);
                    interlaceTrans(i+1,3)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
                end
            end
        end

    %     ignore below till end
        expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''GradientWiseCheck'']/value'];
        expression = xpath.compile(expr);
        status=expression.evaluate(gradMotion,XPathConstants.STRING);

        if strcmp(status,'NA')
            gradientAngle(i+1,:)=NaN(1,3);
            gradientTrans(i+1,:)=NaN(1,3);
        else  
            expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''GradientWiseCheck'']/entry[@parameter=''GradientAngleX'']/green'];
            expression = xpath.compile(expr);
            gradientAngle(i+1,1)=expression.evaluate(gradMotion,XPathConstants.NUMBER);

            expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''GradientWiseCheck'']/entry[@parameter=''GradientAngleY'']/green'];
            expression = xpath.compile(expr);
            gradientAngle(i+1,2)=expression.evaluate(gradMotion,XPathConstants.NUMBER);

            expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''GradientWiseCheck'']/entry[@parameter=''GradientAngleZ'']/green'];
            expression = xpath.compile(expr);
            gradientAngle(i+1,3)=expression.evaluate(gradMotion,XPathConstants.NUMBER);

            if (norm(gradientAngle(i+1,:)+ones(1,3))<eps)
                gradientAngle(i+1,:)=NaN(1,3);
                gradientTrans(i+1,:)=NaN(1,3);
            else
                expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''GradientWiseCheck'']/entry[@parameter=''GradientTranslationX'']/green'];
                expression = xpath.compile(expr);
                gradientTrans(i+1,1)=expression.evaluate(gradMotion,XPathConstants.NUMBER);

                expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''GradientWiseCheck'']/entry[@parameter=''GradientTranslationY'']/green'];
                expression = xpath.compile(expr);
                gradientTrans(i+1,2)=expression.evaluate(gradMotion,XPathConstants.NUMBER);

                expr=['/QCResultSettings/entry[@parameter=''DWI Check'']/entry[@parameter=',gradient,']/entry[@parameter=''GradientWiseCheck'']/entry[@parameter=''GradientTranslationZ'']/green'];
                expression = xpath.compile(expr);
                gradientTrans(i+1,3)=expression.evaluate(gradMotion,XPathConstants.NUMBER);
            end
        end
    end
end
