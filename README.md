# HomeAutomation-DNN
Nest Home Automation, Deep Neural Networks to recognize things of interest to me.  
:point_right:DNN Still WIP:point_left:

# [./Services/](https://github.com/darkmatter2222/HomeAutomation-DNN/tree/main/Services)
## [PubSub_Nest_Subscriber.py](https://github.com/darkmatter2222/HomeAutomation-DNN/blob/main/Services/PubSub_Nest_Subscriber.py)
Running on a Raspberry PI 3b+ as a service as initialized by ./Home_Automation_Services_Startup.sh  
Subscribes to a Google PubSub enpoint with the Google Nest Device Access topic ans write all events to on-prem MongoDB. I have around 2k Events on my property a week:  
  - 3 Outdoor Cameras (Cars/Dogs/People)  
  - 1 Indoor Camera (People)  
  - 1 Thermastat (2x sensors) (Climate control)    
  - 5 Smoke/CO (Info)  
  
:warning:IMPORTANT: This number of events does not charge me anything in GCP. Your milage may vary.:warning:  
I had trouble finding information on how to do all this, below are some step-by-step instructions to get you here:  
  - Create GCP Account [here](https://cloud.google.com/)  
  - Create Nest Device Access (NDA) Account [here](https://developers.google.com/nest/device-access) (One time $5 Fee)  
  - In GCP, create a project  
  - In NDA, create a projact  
  - In GCP, add the PubSub service to your project [here](https://console.cloud.google.com/apis/api/pubsub.googleapis.com)  
  - In GCP, create a GCP Service Account for your PubSub and download the .JSON  
  - Follow code from [here](https://github.com/darkmatter2222/HomeAutomation-DNN/blob/5623760d1d94108ab09f4cb5dd54dba1c4661c15/Services/PubSub_Nest_Subscriber.py#L90)  
    - Have your NDA topic on hand  

## [OAuth_Token_Refresh_Engine.py](https://github.com/darkmatter2222/HomeAutomation-DNN/blob/main/Services/OAuth_Token_Refresh_Engine.py)  
Running on a raspberry PI as a service as Initialized by ./Home_Automation_Services_Startup.sh  
Monitors and automatically refreshes expiring/expiered OAuth2 tokens

