function [H old_Rot old_affine hdr]=get_orient(filename, preferredForm)

   if ~exist('preferredForm','var'), preferredForm= 's'; end     % Jeff
   
   %  Read the dataset header
   [nii.hdr,nii.filetype,nii.fileprefix,nii.machine] = load_nii_hdr(filename);
   hdr = nii.hdr;
   useForm=[];					% Jeff

   if isequal(preferredForm,'S')
       if isequal(hdr.hist.sform_code,0)
           error('User requires sform, sform not set in header');
       else
           useForm='s';
       end
   end						% Jeff

   if isequal(preferredForm,'Q')
       if isequal(hdr.hist.qform_code,0)
           error('User requires sform, sform not set in header');
       else
           useForm='q';
       end
   end						% Jeff

   if isequal(preferredForm,'s')
       if hdr.hist.sform_code > 0
           useForm='s';
       elseif hdr.hist.qform_code > 0
           useForm='q';
       end
   end						% Jeff
   
   if isequal(preferredForm,'q')
       if hdr.hist.qform_code > 0
           useForm='q';
       elseif hdr.hist.sform_code > 0
           useForm='s';
       end
   end						% Jeff
 
   %useForm='q' ;  %%% CHRISTIAN
   
   if isequal(useForm,'s')
      R = [hdr.hist.srow_x(1:3)
           hdr.hist.srow_y(1:3)
           hdr.hist.srow_z(1:3)];

      T = [hdr.hist.srow_x(4)
           hdr.hist.srow_y(4)
           hdr.hist.srow_z(4)];

     old_affine = [ [R;[0 0 0]] [T;1] ];
     old_Rot=old_affine(1:3,1:3);
     H=old_Rot\[0;0;1]; % SZ: i.e. solve H in old_Rot*H=[0;0;1]
     H=H.*[hdr.dime.pixdim(2);hdr.dime.pixdim(3);hdr.dime.pixdim(4)]; % SZ: so that norm(H)=1

   end

