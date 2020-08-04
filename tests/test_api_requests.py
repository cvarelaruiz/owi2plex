from unittest.mock import Mock, patch

import sys
import pytest
from owi2plex import getBouquets
from requests.models import Response
from json.decoder import JSONDecodeError

@patch('owi2plex.requests.get')
def test_getBouquets_single_bouquet(mock_get, bouquet_api_call, openwebif_server):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = bouquet_api_call
    response = getBouquets('TV', openwebif_server, False)
    assert response == {'TV': bouquet_api_call['bouquets'][0][0]}


@patch('owi2plex.requests.get')
def test_getBouquets_no_bouquet(mock_get, bouquet_api_call, openwebif_server):
    mock_get.return_value = Mock(ok=True)
    mock_get.return_value.json.return_value = bouquet_api_call
    response = getBouquets(None, openwebif_server, False)
    bouquet_result = {}
    for b in bouquet_api_call['bouquets']:
        bouquet_result[b[1]] = b[0]
    assert response == bouquet_result


@patch('owi2plex.requests.get')
def test_getBouquets_non_existent(mock_get, bouquet_api_call, openwebif_server):
    mock_get.return_value.ok = True
    mock_get.return_value.json.return_value = bouquet_api_call
    response = getBouquets('-', openwebif_server, False)
    assert response == {}

@patch('owi2plex.requests.get')
def test_getBouquets_error_endpoint(mock_get, openwebif_server):
    mock_response = Response()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    with pytest.raises(JSONDecodeError):
       _ = getBouquets('-', openwebif_server, False)