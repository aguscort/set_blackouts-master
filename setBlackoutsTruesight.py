import json
import requests
import time
import os, sys

class setBlackouts():
    __token = ''
    null = None
    __eps = []
    __apps  = []
    __xmlPath = os.path.join('D:','repos', 'health') #'/home/opsmon/scripts/dashboard/health/'
    __xmlFile = 'truesight_status.html'

    # Constructor and destructor
    def __init__(self, username, password):
        try:
            self.__token = self.__getToken(username, password)            
            self.__apps = self.__getApp()  
        except:
            return None         

    def __getToken(self, username, password): 
        url = 'https://truesightps.prod.oami.eu:8043/tsws/10.0/api/authenticate/login'
        data = '{"username" :"' + username +' ", "password" : "' + password + '", "tenantName" : "BmcRealm"}'
        req = requests.post(url, headers={"Content-Type": "application/json"}, data=data, verify = False).json()
        return req['response']['authToken']


    def __getApp(self): 
        url = 'https://truesightps.prod.oami.eu:8043/tsws/10.0/api/appvis/synthetic/api/applications/getAll?isSynthetic=TRUE'
        req = requests.get(url, headers={"Authorization":"authtoken " + self.__token},verify = False)
        return req.json()
    

    def __getEPbyApp(self, appId): 
        url = 'https://truesightps.prod.oami.eu:8043/tsws/10.0/api/appvis/synthetic/api/executionplans/getAllByApplication?applicationId=' + str(appId)    
        req = requests.get(url, headers={"Authorization":"authtoken " + self.__token},verify = False)
        return req.json()


    def __getEPbyID(self, epId): 
        url = 'https://truesightps.prod.oami.eu:8043/tsws/10.0/api/appvis/synthetic/api/executionplans/getById?executionPlanId=' + str(epId)
        req = requests.get(url, headers={"Authorization":"authtoken " + self.__token},verify = False)
        return req.json()


    def __updateEPbyID(self, payload): 
        url = 'https://truesightps.prod.oami.eu:8043/tsws/10.0/api/appvis/synthetic/api/executionplans/save' 
        headers = {
            "Authorization":"authtoken " + str(self.__token),
            "Content-Type": "application/json"
        }
        req = requests.put(url, data=json.dumps(payload), headers=headers, verify = False)
        return req.status_code


    def __addBlackout(self, epId, begin, end, daysOfWeek, terminateAt, blackoutName): 
        epJson = self.__getEPbyID(epId)   
        epJson['data']['blackOuts'].append({"startAtTimeOffset": "LOCAL", 
            "terminateAt": str(terminateAt), 
            "daysOfRunTillHour": str(end),  
            "daysOfRunFromHour": str(begin), 
            "triggerType": "DAYS_OF_WEEK_BLACKOUT",  
            "daysOfWeek": str(daysOfWeek), 
            "daysOfMonth": self.null, 
            "blackoutName": str(blackoutName), 
            "startAt": "0"})     
        return self.__updateEPbyID(epJson['data'])


    def setfile(self): 
        with open(self.__xmlPath +  self.__xmlFile, 'w') as f:
            f.write('''
                <style type="text/css">
                .tg  {border-collapse:collapse;border-spacing:0;margin:10px auto;width:800px}
                .tg td{font-family:Arial, sans-serif;font-size:14px;padding:4px 20px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:black;}
                .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:4px 20px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:black;}
                .tg .tg-1r1g{background-color:#fe0000;border-color:inherit;vertical-align:top}
                .tg .tg-us36{border-color:inherit;vertical-align:top}
                .tg .tg-ww61{background-color:#34ff34;border-color:inherit;vertical-align:top}
                .tg .tg-iwoe{background-color:#68cbd0;border-color:inherit;vertical-align:top}
                </style>
                <table class="tg">
                <tr><th class="tg-iwoe" colspan="5"><b>Truesight App Status<b></th></tr>
                <tr><td class="tg-iwoe" width="100">Application</td>
                    <td class="tg-iwoe" width="100">executionPlanName</td>
                    <td class="tg-iwoe" width="100">Script</td>
                    <td class="tg-iwoe" width="100">url</td>
                    <td class="tg-iwoe" width="100">Active</td></tr>
                ''')

            for a in self.__apps['data']: # Loop over current Aps
                eps = self.__getEPbyApp(a['id'])                        
                for ep in eps['data']: # Loop over EP in App selected
                    url = ''
                    if ep['scriptFileName'] == 'URLChecker.ltz':
                        for at in range(len(ep['attributes'])):
                            if ep['attributes'][at]['value'].find('http') != -1:
                                url =  ep['attributes'][at]['value']
                                break
                    else: 
                        url = ''

                    if int(str(ep['activeStatus'])) == 1:
                        f.write('<tr><td class="tg-us36">' + a['displayName'] + 
                         '</td><td class="tg-us36">' + ep['executionPlanName'] +
                         '</td><td class="tg-us36">' + ep['scriptFileName'] +
                         '</td><td class="tg-us36">' + str(url) + 
                         '</td><td class="tg-ww61">Active</td></tr>')                   
                    else:
                      f.write('<tr><td class="tg-us36">' + a['displayName'] + 
                         '</td><td class="tg-us36">' + ep['executionPlanName'] + 
                         '</td><td class="tg-us36">' + ep['scriptFileName'] + 
                         '</td><td class="tg-us36">' + url + \
                         '</td><td class="tg-1r1g">Inactive</td></tr>')


            f.write('</table>')
            f.write( time.strftime('<center><p>%d-%m-%Y %H:%M</p></center>')) 



    def addBlackoutSet(self, targetApps, blackoutParameters): 
        for item in range(len(targetApps)):  # Loop over target Apps
            for a in self.__apps['data']: # Loop over current Aps
                if a['displayName'].find(targetApps[item]) != -1: 
                    eps = self.__getEPbyApp(a['id'])                        
                    for ep in eps['data']: # Loop over EP in App selected
                        result = self.__addBlackout(ep['executionPlanId'], blackoutParameters[0], blackoutParameters[1], blackoutParameters[2], blackoutParameters[3], blackoutParameters[4]) # Set Blackout 
                        if result == 200:
                            print ('blackOuts for '  + ep['executionPlanName'] + " (" + ep['executionPlanId'] + ') stated properly')
                        else:                            
                            print ('blackOuts for '  + ep['executionPlanName'] + " (" + ep['executionPlanId'] + ') DIDN\'T state properly')

targetApps = ['BMC']
blackoutParameters = ['09:00', '10:00', '6', '2018-11-19T14:00:00', 'TEST INDOORS']
bk = setBlackouts('', '')
#bk.addBlackoutSet (targetApps, blackoutParameters)
bk.setfile ()