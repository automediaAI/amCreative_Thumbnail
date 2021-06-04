### Juekbox Frame ###
####### v0.1 ########
## . Creates thumbnails for Youtube. Feed it already defined images, and it adds variables on it ##
## . Will create pre defined templates for media type (ie YT etc) and media property (daily feed etc)
## . Uploads to serviceDump airtable, and an AWS link to final asset and saves locally too


## Declarations 
from PIL import Image, ImageDraw, ImageFont
import io
import os
import shortuuid
from airtable import Airtable
from datetime import date, datetime, timedelta
import pytz
import boto3 #to upload image files to S3
from botocore.exceptions import ClientError

## AWS Declarables
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_region='us-west-1' #Manual while creating the bucket 
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

## Airtable settings 
base_key = os.environ.get("PRIVATE_BASE_KEY")
table_name_dump = os.environ.get("PRIVATE_TABLE_NAME_SERVICEDUMP") #Output dump
api_key_airtable = os.environ.get("PRIVATE_API_KEY_AIRTABLE")
airtable_dump = Airtable(base_key, table_name_dump, api_key_airtable)


#Fonts and colors
font_h1 = ImageFont.truetype('Montserrat-Bold.otf', 120)
font_h2 = ImageFont.truetype('Montserrat-Medium.otf', 120)
color_black = (0, 0, 0)
color_white = (255, 255, 255)
color_orange = (254, 80, 0)


pacific_tz = pytz.timezone("America/Los_Angeles")

## Template to create assets 
# For Youtube Thumbnail - CovidFeedDaily 
# today = date.today()
today = datetime.now(pacific_tz)
print(today.tzinfo)
# date_today = today.strftime("%B %d, %Y") #Long full date
date_today = today.strftime("%b %d") #Short MMM-DD 
print(date_today)
# output_filename = 'ytCovidDaily-'+ today.strftime("%b-%d-%Y")

## Main function to create
def create_frame(
	text_entry,
	file_in,
	input_folder, 
	file_type,
	template
	):
	
	# input_file = 'input/'+input_file
	input_file = 'input/'+input_folder+'/'+file_in
	#Loading files or a stream, older code will be files mostly here 
	if file_type == 'stream':
		input_image = Image.open(io.BytesIO(input_file)) #for handling data in ioStream <bytes> format
	else: 
		input_image = Image.open(input_file) #for normal filename

	# input_image.show() #to test it

	# Anchoring where to add text, from https://stackoverflow.com/questions/1970807/center-middle-align-text-with-pil 
	## Template 1 is Date Center, will add more - Needs some minor code changes accordingly
	if template == 'DateCenter':
		W, H = input_image.size #Dimensions if input image 
		draw = ImageDraw.Draw(input_image) #actually create it
		w,h = draw.textsize(text_entry, font=font_h2) #Dimensions of the text
		draw.text(((W-w)/2,((H-h)/2)+50), text_entry, font=font_h2, fill=color_white) #To put in middle but slight off from top

		#Saving ouput
		output_filename = str(file_in)[:-4]+"_Output.png"
		filename_savepath = './output/'+input_folder+'/'+output_filename
		filename_return = output_filename
		
		input_image.save(filename_savepath)
		print ("✅ New image created..")
		return (output_filename, filename_savepath)
	
	else:
		print ('🚫Incorrect template')


# Dumping to AWS 
def dumpToS3(file_name, file_path, bucket='amcreativebucket', object_name=None):
    # If S3 object_name was not specified, use file_name
    url_s3 = f"https://{bucket}.s3-us-west-2.amazonaws.com/{file_name}" #Manually creating structure
    object_name = file_name
    # file_path = './output/'+file_path
    try:
        response = s3.upload_file(file_path, bucket, object_name, ExtraArgs={'ACL':'public-read'}) #Enables public read of file
        print ("✅ Upload to AWS Success: ")
        # print ("✅ Upload to AWS Success: ",url_s3)
        return url_s3
    except ClientError as e:
        print ('🚫Error uploading to S3: '+str(e))
        return ('🚫Error uploading to S3: '+str(e))

# Dumping to service Dump after all is run
def dumpToAirtable(inputURL, input_file):
	time_pulled = str(datetime.now())
	amService = 'amCreative_Thumbnail'
	data_output = str(inputURL)
	UUID = 'ytThumb-'+input_file+'-'+str(shortuuid.uuid()) #to create unique file name
	fields = {'UUID':UUID, 'time_pulled':time_pulled, 'data_output': data_output, 'amService':amService }
	airtable_dump.insert(fields)
	print ("✅ Upload to Airtable Success.")

# Assumes same template for all for now, till we get concept of templates
def runLoop(workingfolder, template):
	path = './input/'+workingfolder+'/'
	files = os.listdir(path)
	for f in files:
		if f[-3:] == 'png':
			# input_file = path+f
			input_file = f
			file_created = create_frame(
				text_entry = date_today,
				file_in = input_file,
				input_folder = workingfolder, 
				file_type = 'file',
				template = 'DateCenter'
				)
			# Getting a tuple back 
			file_name = file_created[0]
			file_path = file_created[1]
			url_uploaded = dumpToS3(file_name, file_path)

runLoop('coviddaily', 'DateCenter')

