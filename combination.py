# Combination script for GBT + ALMA Data
# At the end we smooth ALMA to GBT and feather that to 
# simulate a regular TP+ALMA combination

# Use imhead to determine what need to be regridded/transformed
import glob

myfiles=[]
myfiles=glob.glob('*image*')
mykeys=['cdelt1','cdelt2','cdelt3','cdelt4','restfreq']

for f in myfiles:
     print(f)
     print('------------')
     for key in mykeys:
         q = imhead(f,mode='get',hdkey=key)
         print(str(key)+' : '+str(q))
'''
flagged_image_r_2.0.image
------------
cdelt1 : {'value': -2.42406840554768e-06, 'unit': 'rad'}
cdelt2 : {'value': 2.42406840554768e-06, 'unit': 'rad'}
cdelt3 : {'value': 1.0, 'unit': ''}
cdelt4 : {'value': -28661.91616821289, 'unit': 'Hz'}
restfreq : {'value': 85926263000.0, 'unit': 'Hz'}
PerBolo58_NH2D_gridder_v2_cube_Jybeam.image
------------
cdelt1 : {'value': -9.696273622190623e-06, 'unit': 'rad'}
cdelt2 : {'value': 9.69627362219071e-06, 'unit': 'rad'}
cdelt3 : {'value': 28610.43197631836, 'unit': 'Hz'}
cdelt4 : {'value': 1.0, 'unit': ''}
restfreq : {'value': 85926260000.0, 'unit': 'Hz'}
flagged_image_r_2.0.pb
------------
cdelt1 : {'value': -2.42406840554768e-06, 'unit': 'rad'}
cdelt2 : {'value': 2.42406840554768e-06, 'unit': 'rad'}
cdelt3 : {'value': 1.0, 'unit': ''}
cdelt4 : {'value': -28661.91616821289, 'unit': 'Hz'}
restfreq : {'value': 85926263000.0, 'unit': 'Hz'}

'''

# In your headers, there are three things to note: 
# 1. Axes
# 2. Order of Axes
# 3. Rest Frequency 
# As long as these match, or as long as we can make them 
# match we shouldn't run into any problems when feathering. 

# Regrid GBT Image to match ALMA image

imregrid(imagename='PerBolo58_NH2D_gridder_v2_cube_Jybeam.image',
         template='flagged_image_r_2.0.image',
         axes=[0,1,2],
         output='GBT.image.regrid')

# Reorder the axes of the GBT to match ALMA/pb 

imtrans(imagename='GBT.image.regrid',
        outfile='GBT.image.regrid.ro',
        order='0132')

'''
# (OPTIONAL) RECLEAN ALMA DATA W. GBT AS MODEL

# If you would like to first clean the ALMA data using the GBT image
# as a model, use the following tclean command after regridding and 
# reordering, paying attention to the names in the ALMA subimage command.
# After cleaning, continue the feathering process. 

# Before cleaning, we have to convert the GBT image from Jy/beam to Jy/pixel

bmaj = 9.976
bmin = 9.976 # Note: these are in " so we will include our pixel of 0.5" in our conversion

toJyPerPix = 0.25 / (1.1331 * bmaj * bmin ) # Gaussian to pixel conversion

fluxExpression = "(IM0 * %f)"%(toJyPerPix)
immath(imagename='GBT.regrid.ro/',
       outfile='GBT.Jyperpix',
       mode='evalexpr',
       expr=fluxExpression)

hdval = 'Jy/pixel'
dummy = imhead(imagename='GBT.Jyperpix',
               mode='put',
               hdkey='BUNIT',
               hdvalue=hdval)


myvis='perbol58_nh2d_comb_withflags.ms'
modelvis='GBT.Jyperpix'                   # GBT image in Jy/pixel

tclean(vis=myvis,
       imagename='ALMA_w_GBT_model', 
       field='0,1,2,3,4,5,6,7,8,9,10',
       spw='0,1,2,3,4,5,6,7,8,9,10,11,12',
       phasecenter=3,      
       specmode='cube',
       start='-6km/s',
       width='0.1km/s',
       nchan=200, 
       outframe='lsrk',
       veltype='radio', 
       restfreq='85.926263000GHz', 
       niter=1000,  
       threshold='0.0mJy', 
       interactive=True,
       cell='0.5arcsec',
       imsize=[512,512], 
       weighting='briggs',
       robust=0.5,
       gridder='mosaic',
       pbcor=True,
       restoringbeam='common',
       chanchunks=-1,
       startmodel=modelvis)
'''

# Trim all images to the same size 
# Note: This step is not necessary

imsubimage(imagename='GBT.image.regrid.ro',
           outfile='GBT.image.regrid.ro.subim',
           box='143,143,366,366')

imsubimage(imagename='flagged_image_r_2.0.image',
           outfile='ALMA.image.subim',
           box='143,143,366,366')

imsubimage(imagename='flagged_image_r_2.0.pb',
           outfile='pb.subim', 
           box='143,143,366,366')


# Multiply the flux by the GBT image to get the same response

immath(imagename=['GBT.image.regrid.ro.subim',
                  'pb.subim'],
       expr='IM0*IM1',
       outfile='GBT.multiplied')


# Feather together the GBT*pb and ALMA images

feather(imagename='Feather.image',
        highres='ALMA.image.subim',
        lowres='GBT.multiplied')

###############################################################
# Copy & smooth GBT image to look like TP 
# for 85.9 GHz and 12-m dish size, TP beam will be ~73" 

os.system('cp -r PerBolo58_NH2D_gridder_v2_cube_Jybeam.image GBT.image')
mybeam = {'major': '73.2arcsec', 'minor': '73.2arcsec', 'pa': '0deg'}  
imsmooth( imagename='PerBolo58_NH2D_gridder_v2_cube_Jybeam.image', kernel='gauss', beam=mybeam, targetres=True,outfile='GBT.smooth') 

# Regrid to ALMA image, as before 

imregrid(imagename='GBT.smooth',
         template='flagged_image_r_2.0.image',
         axes=[0,1,2],
         output='GBT.smooth.regrid')

# Still gotta fix that pesky axis...

imtrans(imagename='GBT.smooth.regrid',
        outfile='GBT.smooth.regrid.ro',
        order='0132')


# Trim cube to correct size 

imsubimage(imagename='GBT.smooth.regrid.ro',
           outfile='GBT.smooth.regrid.ro.subim',
           box='143,143,366,366')


# Multiply by primary beam response 

immath(imagename=['GBT.smooth.regrid.ro.subim',
                  'pb.subim'],
       expr='IM0*IM1',
       outfile='GBT.smooth.multiplied')

# Delete the telescope info from the header
 
imhead('GBT.smooth.multiplied',mode='del',hdkey='telescope')

feather(imagename='Feather.smooth.image',
        highres='ALMA.image.subim',
        lowres='GBT.smooth.multiplied')
