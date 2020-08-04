import sys
import os
import pytest


sys.path.append(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope='session')
def openwebif_server():
    return 'openwebif.server'


@pytest.fixture(scope='session')
def bouquet_api_call():
    response = {
        "bouquets": [
            ["1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.ec_tv.tv\" ORDER BY bouquet", "TV"], 
            ["1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.ec_kiddies.tv\" ORDER BY bouquet", "Kiddies"], 
            ["1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.LastScanned.tv\" ORDER BY bouquet", "Last Scanned"], 
            ["1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.favourites.tv\" ORDER BY bouquet", "Sky ROI - Separator"], 
            ["1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.abm.terrestrial_ie_saorview_PSB1.main.tv\" ORDER BY bouquet", "Saorview - All channels"], 
            ["1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.abm.sat_282_freesat.main.tv\" ORDER BY bouquet", "FreeSat UK - FTA HD Channels"], 
            ["1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.abm.sat_282_sky_irl.main.tv\" ORDER BY bouquet", "Sky ROI - FTA HD Channels"], 
            ["1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"userbouquet.abm.sat_282_sky_uk.main.tv\" ORDER BY bouquet", "Sky UK - FTA HD Channels"]
        ]
    }
    return response

