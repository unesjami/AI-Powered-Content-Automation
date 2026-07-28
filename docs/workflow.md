\# System Workflow



\## Overview



AI Telegram Content Automation is an automated pipeline that uses Gemini AI and Telegram Bot API to generate and publish educational technology content.



\---



\## Workflow Process





Images Folder

|

↓

Select Random Images

|

↓

Image Processing

|

↓

Gemini Vision API

|

↓

Generate Persian Caption

|

↓

Add Channel Footer

|

↓

Publish to Telegram Channel

|

↓

Move Image to Used Images

|

↓

Generate Execution Report

|

↓

Send Email Notification





\---



\# Detailed Steps



\## 1. Image Selection



The system scans the images directory and selects random images for processing.



Supported formats:



\- JPG

\- JPEG

\- PNG

\- WEBP



\---



\## 2. AI Caption Generation



Each image is sent to Gemini Vision API.



The AI analyzes the image and creates:



\- Persian educational caption

\- Relevant emojis

\- Technical explanation

\- Hashtags



\---



\## 3. Telegram Publishing



The generated caption is combined with the channel footer and published using Telegram Bot API.



\---



\## 4. Media Management



After successful publishing:



\- The image is moved from `images` to `used\_images`.

\- This prevents duplicate posts.



\---



\## 5. Reporting System



After execution, the system generates a report containing:



\- Number of successful posts

\- Failed operations

\- Execution time

\- Processed images



The report is sent via email.

