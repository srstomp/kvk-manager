# Detects text in a document stored in an S3 bucket. Display polygon box around text and angled text
import boto3
import io
from io import BytesIO
import sys

import math
from PIL import Image, ImageDraw, ImageFont


# Displays information about a block returned by text detection and text analysis
def DisplayBlockInformation(block):
    print('Id: {}'.format(block['Id']))
    if 'Detected' in block:
        print('    Detected: ' + block['Text'])
    print('    Type: ' + block['BlockType'])

    if 'Confidence' in block:
        print('    Confidence: ' + "{:.2f}".format(block['Confidence']) + "%")

    if block['BlockType'] == 'CELL':
        print("    Cell information")
        print("        Column:" + str(block['ColumnIndex']))
        print("        Row:" + str(block['RowIndex']))
        print("        Column Span:" + str(block['ColumnSpan']))
        print("        RowSpan:" + str(block['ColumnSpan']))

    if 'Relationships' in block:
        print('    Relationships: {}'.format(block['Relationships']))
    print('    Geometry: ')
    print('        Bounding Box: {}'.format(block['Geometry']['BoundingBox']))
    print('        Polygon: {}'.format(block['Geometry']['Polygon']))

    if block['BlockType'] == "KEY_VALUE_SET":
        print('    Entity Type: ' + block['EntityTypes'][0])
    if 'Page' in block:
        print('Page: ' + block['Page'])
    print()


if __name__ == "__main__":

    bucket = "reggy-ocr"
    document = "amac.png"

    # Get the document from S3
    s3_connection = boto3.resource('s3')

    s3_object = s3_connection.Object(bucket, document)
    s3_response = s3_object.get()

    stream = io.BytesIO(s3_response['Body'].read())
    image = Image.open(stream)

    # Detect text in the document

    client = boto3.client('textract')
    # process using image bytes
    # image_binary = stream.getvalue()
    # response = client.detect_document_text(Document={'Bytes': image_binary})

    # process using S3 object
    response = client.detect_document_text(
        Document={'S3Object': {'Bucket': bucket, 'Name': document}})

    # Get the text blocks
    blocks = response['Blocks']
    width, height = image.size
    draw = ImageDraw.Draw(image)
    print('Detected Document Text')

    # Create image showing bounding box/polygon the detected lines/text
    for block in blocks:
        print('Type: ' + block['BlockType'])
        if block['BlockType'] != 'PAGE':
            print('Detected: ' + block['Text'])
            print('Confidence: ' + "{:.2f}".format(block['Confidence']) + "%")

        print('Id: {}'.format(block['Id']))
        if 'Relationships' in block:
            print('Relationships: {}'.format(block['Relationships']))
        print('Bounding Box: {}'.format(block['Geometry']['BoundingBox']))
        print('Polygon: {}'.format(block['Geometry']['Polygon']))
        print()
        draw = ImageDraw.Draw(image)
        # Draw WORD - Green -  start of word, red - end of word
        if block['BlockType'] == "WORD":
            draw.line([(width * block['Geometry']['Polygon'][0]['X'],
                        height * block['Geometry']['Polygon'][0]['Y']),
                       (width * block['Geometry']['Polygon'][3]['X'],
                        height * block['Geometry']['Polygon'][3]['Y'])], fill='green',
                      width=2)

            draw.line([(width * block['Geometry']['Polygon'][1]['X'],
                        height * block['Geometry']['Polygon'][1]['Y']),
                       (width * block['Geometry']['Polygon'][2]['X'],
                        height * block['Geometry']['Polygon'][2]['Y'])],
                      fill='red',
                      width=2)

            #draw.polygon([(width * block['Geometry']['Polygon'][0]['X'],
             #              height * block['Geometry']['Polygon'][0]['Y']),
             #             (width * block['Geometry']['Polygon'][1]['X'],
             #              height * block['Geometry']['Polygon'][1]['Y']),
             #             (width * block['Geometry']['Polygon'][2]['X'],
             #              height * block['Geometry']['Polygon'][2]['Y']),
             #             (width * block['Geometry']['Polygon'][3]['X'],
             #              height * block['Geometry']['Polygon'][3]['Y'])], fill=(10,10,25,0))

            # Draw box around entire LINE
        if block['BlockType'] == "LINE":
            points = []

            for polygon in block['Geometry']['Polygon']:
                points.append((width * polygon['X'], height * polygon['Y']))

            draw.polygon((points), outline='black')

            # Uncomment to draw bounding box
            box=block['Geometry']['BoundingBox']
            left = width * box['Left']
            top = height * box['Top']
            draw.rectangle([left,top, left + (width * box['Width']), top +(height * box['Height'])],outline='black')

    # Display the image
    image.show()





