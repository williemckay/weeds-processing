from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection, FeatureLayer
from copy import deepcopy
from pathlib import Path
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import smtplib, configparser, sys, traceback


sys.path.append(r"C:\Scripts\shared")
sys.stdout.reconfigure(encoding='utf-8')

from heartbeat import mark_success, mark_failure, mark_started

TASK_NAME = "Weeds_AGOL_pythonProcesses"

mark_started(TASK_NAME)


def send_email(subject, body, recipients=None):
    if recipients is None:
        recipients = ["william.mckay@horizons.govt.nz", "courtney.tregurtha-nairn@horizons.govt.nz"]
        
    sender = "william.mckay@horizons.govt.nz"
    
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    
    message.attach(MIMEText(body, "plain"))
    
    mailServer = smtplib.SMTP("mail.horizons.govt.nz")
    mailServer.send_message(message)
    mailServer.quit()


try:
    print("Accessing AGOL data")
    
    config =configparser.ConfigParser()
    config.read(r'C:\Scripts\CONFIG\config.ini')
    
    AGOL_portal = config['AGOL']['AGOL_portal']
    AGOL_username = config['AGOL']['AGOL_username']
    AGOL_password = config['AGOL']['AGOL_password']
    AGOL_profile = AGOL_username
    
    gis = GIS(AGOL_portal, AGOL_username, AGOL_password)
    
    
    weeds = gis.content.get('c3188f713dc8484ab68df07ef86c40a9')
    
    
    inspection = weeds.tables[0]
    site = weeds.layers[0]
    
    #If I want to view the table in a dataframe
    tableDf = inspection.query(where="1=1",out_fields="*").sdf
    
    
    siteDf = site.query(where="1=1", out_fields="*").sdf
    
    ############## COPY BASE SITE ID FROM PARENT ######################
    
    #Copy Base site from BaseSiteID field in site table to BaseSiteID field in inspection table
    print("Copying BASESiteID from Parent table") 
    copyBaseSite_site = siteDf.copy()
    copyBaseSiteInspection = tableDf.copy()
    
    
    #Detect new features in the inspection table which have no BaseSiteID and take a copy of these features
    #Actually this could be used as general updates for new records in the site table so make sure that this captures everything
    #For example this won't catch if existing records are edited...
    new_inspection_SiteID = copyBaseSiteInspection[copyBaseSiteInspection["BaseSiteID"].isna()].copy()
    
    
    
    #GlobalID from site table is the primary key and ParentGlobalID from inspection table is the foreign key
    baseSiteID_Join = copyBaseSite_site.merge(new_inspection_SiteID,
                            left_on = 'GlobalID',
                            right_on = 'ParentGlobalID',
                            how = 'right',
                            suffixes = ('_site','_inspection')
                                            )
    
    # Copy BaseSiteID_site to BaseSiteID_inspection
    baseSiteID_Join['BaseSiteID_inspection'] = baseSiteID_Join['BaseSiteID_site']
    
    
    #Munge baseSiteID_Join down to a dataframe matching tableDf and then can update inspection 
    
    rename_mapInspection = {
        "OBJECTID_inspection": "OBJECTID",   
        "operatorName_inspection": "operatorName",
        "who_inspection":"who",
        "address_inspection":"address",
        "occupancyArea_inspection":"occupancyArea",
        "cultivated_inspection":"cultivated",
        "occupancyExtent_inspection":"occupancyExtent",
        "UID_inspection":"UID",
        "CreationDate_inspection":"CreationDate",
        "Creator_inspection":"Creator",
        "EditDate_inspection":"EditDate",
        "Editor_inspection":"Editor",
        "BaseSiteID_inspection":"BaseSiteID",
        "GlobalID_inspection":"GlobalID",
        "Creator_1_inspection":"Creator_1",
        "EditDate_1_inspection":"EditDate_1",
        "Editor_1_inspection":"Editor_1"
    }
    
    baseSiteID_Join_renamed = baseSiteID_Join.rename(columns=rename_mapInspection)
    
    # Get the list of columns from tableDf
    cols_to_keep = tableDf.columns
    
    # Reduce joined flat table to only those columns (drop the rest)
    BSID_update = baseSiteID_Join_renamed[cols_to_keep]
    
    #Use fillna so that there are no Null values
    #BSID_update['BaseSiteID'] = BSID_update['BaseSiteID'].fillna('NoID')
    BSID_update.loc[BSID_update["BaseSiteID"].isna(), "BaseSiteID"] = "NoID"
    
    ##Reduce the dataframe so that only the field we want to update and objectID are retained
    BSID_update = BSID_update[["OBJECTID","BaseSiteID"]]
    
    #Convert dataframe to dictionary so that it can be updated in AGOL
    baseSiteID_updates = [
        {"attributes": row.to_dict()}
        for _, row in BSID_update.iterrows()
    ]
    
    if baseSiteID_updates:
        resultBaseSiteID = inspection.edit_features(updates=baseSiteID_updates)
        print("Edits applied to update base site ID:", baseSiteID_updates)
    else:
        print("No changes detected for updating base site ID.")
        
        
    ########### COPY INSPECTION ID TO LEGACY SITE ID ################
    print("Copying InspectionID to Legacy SiteID")
    inspectionDf = tableDf.copy()
    
    new_inspection_InspectionID = inspectionDf[inspectionDf["Legacy_SiteID"].isna()].copy()
    
    #Copy inspectionID to LegacySiteID
    new_inspection_InspectionID['Legacy_SiteID'] = new_inspection_InspectionID['InspectionID']
    #inspectionDf.loc[inspectionDf['Legacy_SiteID'].isna(), 'Legacy_SiteID'] = inspectionDf['InspectionID']
    
    new_inspection_InspectionID['Legacy_SiteID'] = new_inspection_InspectionID['Legacy_SiteID'].fillna('NoID')
    new_inspection_InspectionID = new_inspection_InspectionID[["OBJECTID","Legacy_SiteID"]]
    
    inspectionID_updates = [
        {"attributes": row.to_dict()}
        for _, row in new_inspection_InspectionID.iterrows()
    ]
    
    if inspectionID_updates:
        resultInspectionID = inspection.edit_features(updates=inspectionID_updates)
        print("Edits applied for new inspection IDs:", inspectionID_updates)
    else:
        print("No changes detected for new inspection IDs.")
        
        
        
    ############### POPULATE RECORD END DATE ######################
    print("Populating record end dates")
    weeds_2 = gis.content.get('c3188f713dc8484ab68df07ef86c40a9')
    
    
    inspection_2 = weeds_2.tables[0]
    
    
    recordEndDate = inspection_2.query(where="1=1",out_fields="*").sdf
    recordEndDate.loc[recordEndDate['recordEndDate'].isna(), 'hasEndDate'] = 0
    
    dupeCheck = recordEndDate.query('hasEndDate == 0')
    
    noEndDateDupes = dupeCheck[['OBJECTID','BaseSiteID','InspectionID','recordEndDate','revisitNumber','inspectionDate']]
    dupes = noEndDateDupes[noEndDateDupes.duplicated(subset=["BaseSiteID"], keep=False)].copy()
    
    dupes['updateFrom'] = dupes['revisitNumber'] - 1
    #dupes = dupes.query('updateFrom > 0')
    dupesCopyDate = dupes.copy()
    dupesCopyDate['updateFrom'] = dupesCopyDate['updateFrom'].astype(str)
    dupesCopyDate['inspectionToUpdate'] = dupesCopyDate['BaseSiteID'] + "-" + dupesCopyDate['updateFrom']
    dupesCopyDate = dupesCopyDate.query('updateFrom!="0"')
    dupesCopyDate = dupesCopyDate[['inspectionToUpdate','inspectionDate']]
    
    
    dupesForUpdate = dupes[['OBJECTID','InspectionID','recordEndDate']]
    
    updateRecordEndDates = dupesCopyDate.merge(dupesForUpdate,
                                            left_on = 'inspectionToUpdate',
                                            right_on = 'InspectionID',
                                            how = 'inner')
    
    updateRecordEndDates['recordEndDate'] = updateRecordEndDates['inspectionDate']
    
    updateRecordEndDates = updateRecordEndDates[['OBJECTID','recordEndDate']]
    
    updateRecordEndDates
    
    #ready for Dictionary and update statement
    recordEndDate_updates = [
        {"attributes": row.to_dict()}
        for _, row in updateRecordEndDates.iterrows()
    ]
    
    if recordEndDate_updates:
        resultRecordEndDate = inspection.edit_features(updates=recordEndDate_updates)
        print("Edits applied to record end date:", recordEndDate_updates)
    else:
        print("No changes detected for record end date.")
    
    
    
    
    #################### SYNC PARENT CONTACT LATEST NON BLANK #####################
    print("Syncing contacts up to site record")
    #for each BaseSiteID in inspection table  set all blanks to the latest Non-Blank value by revisitNumber for who, address, and phone number fields
    
    site_2 = weeds_2.layers[0]
    
    
    tableDf_2 = inspection_2.query(where="1=1",out_fields="*").sdf
    
    siteDf_2 = site_2.query(where="1=1", out_fields="*").sdf
    
    syncConts = tableDf_2[['OBJECTID','BaseSiteID','who','address','PhoneNumber','revisitNumber','InspectionID']].copy()
    syncContsSite = siteDf_2[['OBJECTID','BaseSiteID','currentWho','currentAddress','currentContactPhone']].copy()
    
    lastInspection = syncConts.groupby(['BaseSiteID'],as_index=False)['revisitNumber'].max()
    
    lastInspection['revisitNumber'] = lastInspection['revisitNumber'].astype(str)
    
    lastInspection['InspectionID'] = lastInspection['BaseSiteID'] + "-" + lastInspection['revisitNumber']
    lastSiteInspection = lastInspection[['InspectionID']]
    lastSiteInspection
    
    #Now use this list to lookup the inspectionIDs in the inspectionTable
    lastInspection = syncConts[syncConts["InspectionID"].isin(lastSiteInspection["InspectionID"])]
    lastInspection
    
    #Join on BaseSiteID to the site table
    JoinedContData = syncContsSite.merge(
                        lastInspection,
                        on = 'BaseSiteID',
                        how = 'right')
                        
    
    #Identify where who, address or phone numbers don't match
    JoinedContData['currentWho'].fillna("",inplace=True)
    JoinedContData['currentAddress'].fillna("",inplace=True)
    JoinedContData['currentContactPhone'].fillna("",inplace=True)
    
    updateWho = JoinedContData[JoinedContData['currentWho']!=JoinedContData['who']].copy()
    updateWho.loc[updateWho["currentWho"] != updateWho["who"], "currentWho"] = updateWho["who"]
    
    updateAddress = JoinedContData[JoinedContData['currentAddress']!=JoinedContData['address']].copy()
    updateAddress.loc[updateAddress["currentAddress"] != updateAddress["address"], "currentAddress"] = updateAddress["address"]
    
    updatePhone = JoinedContData[JoinedContData['currentContactPhone']!=JoinedContData['PhoneNumber']].copy()
    updatePhone.loc[updatePhone["currentContactPhone"] != updatePhone["PhoneNumber"], "currentContactPhone"] = updatePhone["PhoneNumber"]
    
    
    updateWhoDf = updateWho[['OBJECTID_x','currentWho']].copy()
    updateWhoDf.rename(columns = {'OBJECTID_x':'OBJECTID'},inplace=True)
    
    updateAddressDf = updateAddress[['OBJECTID_x','currentAddress']].copy()
    updateAddressDf.rename(columns = {'OBJECTID_x':'OBJECTID'},inplace=True)
    
    updatePhoneDf = updatePhone[['OBJECTID_x','currentContactPhone']].copy()
    updatePhoneDf.rename(columns = {'OBJECTID_x':'OBJECTID'},inplace=True)
    
    
    #Create Dictionaries
    contactWho_updates = [
        {"attributes": row.to_dict()}
        for _, row in updateWhoDf.iterrows()
    ]
    
    contactAddress_updates = [
        {"attributes": row.to_dict()}
        for _, row in updateAddressDf.iterrows()
    ]
    contactPhone_updates = [
        {"attributes": row.to_dict()}
        for _, row in updatePhoneDf.iterrows()
    ]
    
    
    #Write to FeatureService
    if contactWho_updates:
        resultWho = site.edit_features(updates=contactWho_updates)
        print("Edits applied for updating contact name:", contactWho_updates)
    else:
        print("No changes detected for updating contact name.")
        
        
    if contactAddress_updates:
        resultAddress = site.edit_features(updates=contactAddress_updates)
        print("Edits applied for updating contact address:", contactAddress_updates)
    else:
        print("No changes detected for updating contact address.")
    
        
    if contactPhone_updates:
        resultPhone = site.edit_features(updates=contactPhone_updates)
        print("Edits applied for updating contact phone number:", contactPhone_updates)
    else:
        print("No changes detected for updating contact phone number.")
    
    
    #################### Update currentSiteStatus in site table #####################
    
    weeds_3 = gis.content.get('c3188f713dc8484ab68df07ef86c40a9')
    
    
    inspection_3 = weeds_3.tables[0]
    site_3 = weeds_3.layers[0]
    
    #If I want to view the table in a dataframe
    tableDf_3 = inspection_3.query(where="1=1",out_fields="*").sdf
    
    
    siteDf_3 = site_3.query(where="1=1", out_fields="*").sdf
    
    siteStatus = siteDf_3[['OBJECTID','BaseSiteID','currentSiteStatus']].copy()
    inspectionStatus = tableDf_3[['BaseSiteID','InspectionID','revisitNumber','siteStatus']].copy()
    
    siteOAA = siteDf_3[['OBJECTID','BaseSiteID','currentOccupancyArea']].copy()
    inspectionOAA = tableDf_3[['BaseSiteID','InspectionID','revisitNumber','occupancyArea']].copy()
    
    lastInspection = inspectionStatus.groupby(['BaseSiteID'],as_index=False)['revisitNumber'].max()
    
    lastInspection['revisitNumber'] = lastInspection['revisitNumber'].astype(str)
    
    lastInspection['InspectionID'] = lastInspection['BaseSiteID'] + "-" + lastInspection['revisitNumber']
    lastSiteInspection = lastInspection[['InspectionID']]
    #lastSiteInspection
    
    #Now use this list to lookup the inspectionIDs in the inspectionTable
    lastInspection = inspectionStatus[inspectionStatus["InspectionID"].isin(lastSiteInspection["InspectionID"])]
    lastInspectionOAA = inspectionOAA[inspectionOAA["InspectionID"].isin(lastSiteInspection["InspectionID"])]
    #lastInspection
    
    #Join on BaseSiteID to the site table
    JoinedStatusData = siteStatus.merge(
                        lastInspection,
                        on = 'BaseSiteID',
                        how = 'right')
                        
    JoinedStatusData['currentSiteStatus'].fillna("",inplace=True)
    
    JoinedOAAData = siteOAA.merge(
                        lastInspectionOAA,
                        on = 'BaseSiteID',
                        how = 'right')
                        
    JoinedOAAData['currentOccupancyArea'].fillna(0,inplace=True)
    
    
    updateStatus = JoinedStatusData[JoinedStatusData['currentSiteStatus']!=JoinedStatusData['siteStatus']].copy()
    updateStatus.loc[updateStatus["currentSiteStatus"] != updateStatus["siteStatus"], "currentSiteStatus"] = updateStatus["siteStatus"]
    updateStatus = updateStatus[updateStatus['OBJECTID'].notna()]
    
    updateOAA = JoinedOAAData[JoinedOAAData['currentOccupancyArea']!=JoinedOAAData['occupancyArea']].copy()
    updateOAA.loc[updateOAA["currentOccupancyArea"] != updateOAA["occupancyArea"], "currentOccupancyArea"] = updateOAA["occupancyArea"]
    updateOAA = updateOAA[updateOAA['OBJECTID'].notna()]
    
    #updateOAA = updateOAA.rename(columns = {'occupancyArea_x':'occupancyArea'})
    
    updateStatusDf = updateStatus[['OBJECTID','currentSiteStatus']].copy()
    updateOAA_df = updateOAA[['OBJECTID','currentOccupancyArea']].copy()
    
    
    
    
    
    #Create Dictionaries
    siteStatus_updates = [
        {"attributes": row.to_dict()}
        for _, row in updateStatusDf.iterrows()
    ]
    
    siteOAA_updates = [
        {"attributes": row.to_dict()}
        for _, row in updateOAA_df.iterrows()
    ]
    
    
    ##Write to FeatureService
    if siteStatus_updates:
        resultSiteStatus = site.edit_features(updates=siteStatus_updates)
        print("Edits applied for updating currentSiteStatus:", siteStatus_updates)
    else:
        print("No changes detected for updating currentSiteStatus.")
        
    if siteOAA_updates:
        resultSiteOAA = site.edit_features(updates=siteOAA_updates)
        print("Edits applied for updating currentSiteStatus:", siteOAA_updates)
    else:
        print("No changes detected for updating OAA.")
        
        
    ######################### Populate EOO
    #For a parent site where EOO is blank, calculate this from shape.area with 0dp - for populating where new sites are made offline
    siteDf_Eoo = siteDf.copy()
    
    siteDf_Eoo['occupancyExtent'].fillna(0,inplace=True)
    unknownEOO = siteDf_Eoo.query('occupancyExtent == 0')
    
    unknownEOO['occupancyExtent'] = unknownEOO['Shape__Area'].round(0)
    unknownEOO['occupancyExtent'].fillna(0,inplace=True)
    
    eooUpdate = unknownEOO[['OBJECTID','occupancyExtent']]
    
    eooUpdate_updates = [
        {"attributes": row.to_dict()}
        for _, row in eooUpdate.iterrows()
    ]
    
    if eooUpdate_updates:
        resultEooUpdates = site.edit_features(updates=eooUpdate_updates)
        print("Edits applied to occupancyExtent:", eooUpdate_updates)
    else:
        print("No changes detected for occupancyExtent.")


    ###########################Populate Nulls
    inspection_df = tableDf.copy()
    site_sdf = siteDf.copy()

    stringFields = [
        'bioAgentSelfEst',
        'Nursery',
        'Present',
        'Damage'
    ]

    intFields = [
        'adultCount',
        'juvenileCount',
        'seedlingCount',
        'largeSizeCount',
        'mediumSizeCount',
        'smallSizeCount',
        'ExtraSmallSizeCount'
    ]

    inspectionStringNull = inspection_df[inspection_df[stringFields].isna().any(axis=1)]
    inspectionIntNull = inspection_df[inspection_df[intFields].isna().any(axis=1)]
    siteNull = site_sdf[site_sdf['cultivated'].isna()]

    inspectionStringNull[stringFields] = inspectionStringNull[stringFields].fillna('N')
    inspectionIntNull[intFields] = inspectionIntNull[intFields].fillna(0)

    siteNull['cultivated'] = siteNull['cultivated'].fillna('N')


    inspectionString = inspectionStringNull[[
        'OBJECTID',
        'bioAgentSelfEst',
        'Nursery',
        'Present',
        'Damage'
    ]]

    inspectionInt = inspectionIntNull[[
        'OBJECTID',
        'adultCount',
        'juvenileCount',
        'seedlingCount',
        'largeSizeCount',
        'mediumSizeCount',
        'smallSizeCount',
        'ExtraSmallSizeCount'
    ]]

    siteCultNull = siteNull[[
        'OBJECTID',
        'cultivated'
    ]]

    #create dictionaries
    inspectionString_updates = [
            {"attributes": row.to_dict()}
            for _, row in inspectionString.iterrows()
        ]

    inspectionInt_updates = [
            {"attributes": row.to_dict()}
            for _, row in inspectionInt.iterrows()
        ]

    siteNull_updates = [
            {"attributes": row.to_dict()}
            for _, row in siteCultNull.iterrows()
        ]  


    if inspectionString_updates:
        result_inspectionStringUpdates = inspection.edit_features(updates=inspectionString_updates)
        print("Edits applied to Null string values in Inspection table:", inspectionString_updates)
    else:
        print("No changes detected for  Null string values in Inspection table.")


    if inspectionInt_updates:
        result_inspectionIntUpdates = inspection.edit_features(updates=inspectionInt_updates)
        print("Edits applied to Null integer values in Inspection table:", inspectionInt_updates)
    else:
        print("No changes detected for Null integer values in Inspection table.")


    if siteNull_updates:
        result_siteNullUpdates = site.edit_features(updates=siteNull_updates)
        print("Edits applied to Null cultivated values:", siteNull_updates)
    else:
        print("No changes detected for Null cultivated values.") 
    
    mark_success(TASK_NAME)
    
    
except Exception:
    error_text = traceback.format_exc()
    failures = mark_failure(TASK_NAME, error_text)
    
    if failures == 1:
        send_email(
            subject=f"WARNING: {TASK_NAME} failed once",
            body=f"""
            {TASK_NAME} has failed once.
            
            This may be a temporary AGOL timeout or server hiccup.
            
            Consecutive failures: {failures}
            
            Error:
            {error_text}
            """
            )
            
    elif failures >= 2:
        send_email(
            subject = f"CRITICAL: {TASK_NAME} failed {failures} times in a row",
            body = f"""
            {TASK_NAME} has failed {failures} times in a row.
            
            This now needs investigation.
            
            Check:
            - Task scheduler status
            - AGOL connection/authentication (including ArcGIS Pro)
            - server/network connection
            - recent schema/domain changes
            - log file output
            
            Error:
            {error_text}
            """
            )
            
    raise