#!/usr/bin/env python3
import os, sys, subprocess, base64, json, time

BASE = "/home/user/VPS-ClaudeCode"
BOT_B64 = "cmVxdWlyZSgnZG90ZW52JykuY29uZmlnKCk7CmNvbnN0IHsgQm90LCBLZXlib2FyZCwgSW5saW5lS2V5Ym9hcmQgfSA9IHJlcXVpcmUoJ2dyYW1teScpOwpjb25zdCB7IHJ1bkNsYXVkZSB9ID0gcmVxdWlyZSgnLi9jbGF1ZGUtcnVubmVyJyk7CmNvbnN0IHsgZXhlY1N5bmMgfSA9IHJlcXVpcmUoJ2NoaWxkX3Byb2Nlc3MnKTsKY29uc3QgZnMgPSByZXF1aXJlKCdmcycpOwpjb25zdCBodHRwcyA9IHJlcXVpcmUoJ2h0dHBzJyk7CgovLyDQn9C+0YHRgtC+0Y/QvdC90LDRjyDQutC70LDQstC40LDRgtGD0YDQsCDQsdGL0YHRgtGA0L7Qs9C+INC00L7RgdGC0YPQv9CwCmNvbnN0IE1BSU5fS0VZQk9BUkQgPSBuZXcgS2V5Ym9hcmQoKQogIC50ZXh0KCfwn5OKINCb0L7Qs9C4JykudGV4dCgn8J+TgSDQpNCw0LnQu9GLJykudGV4dCgn8J+TjSDQk9C00LUg0Y8nKS5yb3coKQogIC50ZXh0KCfwn5SEINCd0L7QstCw0Y8g0YHQtdGB0YHQuNGPJykudGV4dCgn4puUINCe0YLQvNC10L3QsCcpLnRleHQoJ/CflI0g0J/QuNC90LMnKQogIC5yZXNpemVkKCkKICAucGVyc2lzdGVudCgpOwoKY29uc3QgVE9LRU4gPSBwcm9jZXNzLmVudi5URUxFR1JBTV9CT1RfVE9LRU47CmNvbnN0IEFMTE9XRURfSURTID0gKHByb2Nlc3MuZW52LkFMTE9XRURfVVNFUl9JRFMgfHwgJycpCiAgLnNwbGl0KCcsJykubWFwKHMgPT4gcy50cmltKCkpLmZpbHRlcihCb29sZWFuKS5tYXAoTnVtYmVyKTsKY29uc3QgVVBEQVRFX0lOVEVSVkFMID0gcGFyc2VJbnQocHJvY2Vzcy5lbnYuU1RSRUFNX1VQREFURV9JTlRFUlZBTF9NUyB8fCAnMjAwMCcsIDEwKTsKY29uc3QgV09SS19ESVIgPSBwcm9jZXNzLmVudi5XT1JLX0RJUiB8fCBwcm9jZXNzLmN3ZCgpOwpjb25zdCBPUEVOQUlfQVBJX0tFWSA9IHByb2Nlc3MuZW52Lk9QRU5BSV9BUElfS0VZIHx8ICcnOwoKaWYgKCFUT0tFTikgeyBjb25zb2xlLmVycm9yKCdURUxFR1JBTV9CT1RfVE9LRU4gbm90IHNldCcpOyBwcm9jZXNzLmV4aXQoMSk7IH0KCmNvbnN0IGJvdCA9IG5ldyBCb3QoVE9LRU4pOwpjb25zdCBzZXNzaW9ucyA9IG5ldyBNYXAoKTsKY29uc3QgaW5GbGlnaHQgPSBuZXcgTWFwKCk7CgpmdW5jdGlvbiBpc0FsbG93ZWQoaWQpIHsKICByZXR1cm4gQUxMT1dFRF9JRFMubGVuZ3RoID09PSAwIHx8IEFMTE9XRURfSURTLmluY2x1ZGVzKGlkKTsKfQoKZnVuY3Rpb24gc3BsaXRUZXh0KHRleHQsIG1heExlbikgewogIGNvbnN0IHBhcnRzID0gW107CiAgbGV0IGkgPSAwOwogIHdoaWxlIChpIDwgdGV4dC5sZW5ndGgpIHsgcGFydHMucHVzaCh0ZXh0LnNsaWNlKGksIGkgKyBtYXhMZW4pKTsgaSArPSBtYXhMZW47IH0KICByZXR1cm4gcGFydHM7Cn0KCmZ1bmN0aW9uIHNhZmVFZGl0KGN0eCwgY2hhdElkLCBtc2dJZCwgdGV4dCkgewogIHJldHVybiBjdHguYXBpLmVkaXRNZXNzYWdlVGV4dChjaGF0SWQsIG1zZ0lkLCB0ZXh0IHx8ICfigKYnKS5jYXRjaCgoKSA9PiB7fSk7Cn0KCi8vIERvd25sb2FkIGZpbGUgZnJvbSBUZWxlZ3JhbQpmdW5jdGlvbiBkb3dubG9hZEZpbGUodXJsLCBkZXN0KSB7CiAgcmV0dXJuIG5ldyBQcm9taXNlKChyZXNvbHZlLCByZWplY3QpID0+IHsKICAgIGNvbnN0IGZpbGUgPSBmcy5jcmVhdGVXcml0ZVN0cmVhbShkZXN0KTsKICAgIGh0dHBzLmdldCh1cmwsIChyZXMpID0+IHsKICAgICAgcmVzLnBpcGUoZmlsZSk7CiAgICAgIGZpbGUub24oJ2ZpbmlzaCcsICgpID0+IHsgZmlsZS5jbG9zZSgpOyByZXNvbHZlKCk7IH0pOwogICAgfSkub24oJ2Vycm9yJywgcmVqZWN0KTsKICB9KTsKfQoKLy8gVHJhbnNjcmliZSB2b2ljZSB2aWEgT3BlbkFJIFdoaXNwZXIKYXN5bmMgZnVuY3Rpb24gdHJhbnNjcmliZVZvaWNlKGZpbGVQYXRoKSB7CiAgaWYgKCFPUEVOQUlfQVBJX0tFWSkgdGhyb3cgbmV3IEVycm9yKCdPUEVOQUlfQVBJX0tFWSDQvdC1INC90LDRgdGC0YDQvtC10L0g0LIgLmVudicpOwogIGNvbnN0IEZvcm1EYXRhID0gcmVxdWlyZSgnZm9ybS1kYXRhJyk7CiAgY29uc3QgZm9ybSA9IG5ldyBGb3JtRGF0YSgpOwogIGZvcm0uYXBwZW5kKCdmaWxlJywgZnMuY3JlYXRlUmVhZFN0cmVhbShmaWxlUGF0aCksIHsgZmlsZW5hbWU6ICd2b2ljZS5vZ2cnLCBjb250ZW50VHlwZTogJ2F1ZGlvL29nZycgfSk7CiAgZm9ybS5hcHBlbmQoJ21vZGVsJywgJ3doaXNwZXItMScpOwogIGZvcm0uYXBwZW5kKCdsYW5ndWFnZScsICdydScpOwoKICByZXR1cm4gbmV3IFByb21pc2UoKHJlc29sdmUsIHJlamVjdCkgPT4gewogICAgY29uc3QgcmVxID0gaHR0cHMucmVxdWVzdCh7CiAgICAgIGhvc3RuYW1lOiAnYXBpLm9wZW5haS5jb20nLAogICAgICBwYXRoOiAnL3YxL2F1ZGlvL3RyYW5zY3JpcHRpb25zJywKICAgICAgbWV0aG9kOiAnUE9TVCcsCiAgICAgIGhlYWRlcnM6IHsgLi4uZm9ybS5nZXRIZWFkZXJzKCksIEF1dGhvcml6YXRpb246ICdCZWFyZXIgJyArIE9QRU5BSV9BUElfS0VZIH0sCiAgICB9LCAocmVzKSA9PiB7CiAgICAgIGxldCBkYXRhID0gJyc7CiAgICAgIHJlcy5vbignZGF0YScsIGNodW5rID0+IHsgZGF0YSArPSBjaHVuazsgfSk7CiAgICAgIHJlcy5vbignZW5kJywgKCkgPT4gewogICAgICAgIHRyeSB7CiAgICAgICAgICBjb25zdCBqc29uID0gSlNPTi5wYXJzZShkYXRhKTsKICAgICAgICAgIGlmIChqc29uLnRleHQpIHJlc29sdmUoanNvbi50ZXh0KTsKICAgICAgICAgIGVsc2UgcmVqZWN0KG5ldyBFcnJvcihqc29uLmVycm9yICYmIGpzb24uZXJyb3IubWVzc2FnZSB8fCAnV2hpc3BlciBlcnJvcicpKTsKICAgICAgICB9IGNhdGNoIHsgcmVqZWN0KG5ldyBFcnJvcignV2hpc3BlciBwYXJzZSBlcnJvcicpKTsgfQogICAgICB9KTsKICAgIH0pOwogICAgcmVxLm9uKCdlcnJvcicsIHJlamVjdCk7CiAgICBmb3JtLnBpcGUocmVxKTsKICB9KTsKfQoKLy8g4pSA4pSA4pSAIENvbW1hbmRzIOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgOKUgAoKYm90LmNvbW1hbmQoJ3N0YXJ0JywgY3R4ID0+IGN0eC5yZXBseSgKICAnQ2xhdWRlIENvZGUgQnJpZGdlXG5cbicgKwogICfQntGC0L/RgNCw0LLRjCDQt9Cw0LTQsNGH0YMg0YLQtdC60YHRgtC+0Lwg0LjQu9C4INCz0L7Qu9C+0YHQvtC8IOKAlCDQstGL0L/QvtC70L3RjiDQvdCwIFZQUy5cblxuJyArCiAgJ9Ca0L3QvtC/0LrQuCDQsdGL0YHRgtGA0L7Qs9C+INC00L7RgdGC0YPQv9CwINC/0L7Rj9Cy0Y/RgtGB0Y8g0LLQvdC40LfRgyDRjdC60YDQsNC90LAuJywKICB7IHJlcGx5X21hcmt1cDogTUFJTl9LRVlCT0FSRCB9CikpOwoKLy8g0JrQvdC+0L/QutC4INC60LvQsNCy0LjQsNGC0YPRgNGLCmJvdC5oZWFycygn8J+TiiDQm9C+0LPQuCcsIGFzeW5jIGN0eCA9PiB7CiAgdHJ5IHsKICAgIGNvbnN0IG91dCA9IGV4ZWNTeW5jKCd0YWlsIC0zMCAvcm9vdC8ucG0yL2xvZ3MvY2xhdWRlLXRlbGVncmFtLWJyaWRnZS1vdXQubG9nIDI+L2Rldi9udWxsIHx8IGVjaG8gItCb0L7QsyDQv9GD0YHRgiInLCB7IGVuY29kaW5nOiAndXRmOCcgfSkuc2xpY2UoLTM1MDApOwogICAgYXdhaXQgY3R4LnJlcGx5KG91dCB8fCAn0JvQvtCz0Lgg0L/Rg9GB0YLRiy4nKTsKICB9IGNhdGNoIChlKSB7IGF3YWl0IGN0eC5yZXBseSgn0J7RiNC40LHQutCwOiAnICsgZS5tZXNzYWdlKTsgfQp9KTsKYm90LmhlYXJzKCfwn5OBINCk0LDQudC70YsnLCBhc3luYyBjdHggPT4gewogIHRyeSB7CiAgICBjb25zdCBvdXQgPSBleGVjU3luYygnZmluZCAnICsgV09SS19ESVIgKyAnIC1uZXdlciAnICsgV09SS19ESVIgKyAnL3BhY2thZ2UuanNvbiAtdHlwZSBmIC1ub3QgLXBhdGggIiovbm9kZV9tb2R1bGVzLyoiIC1ub3QgLXBhdGggIiovLmdpdC8qIiAyPi9kZXYvbnVsbCB8IGhlYWQgLTIwJywgeyBlbmNvZGluZzogJ3V0ZjgnIH0pOwogICAgYXdhaXQgY3R4LnJlcGx5KG91dC50cmltKCkgfHwgJ9CY0LfQvNC10L3RkdC90L3Ri9GFINGE0LDQudC70L7QsiDQvdC10YIuJyk7CiAgfSBjYXRjaCAoZSkgeyBhd2FpdCBjdHgucmVwbHkoJ9Ce0YjQuNCx0LrQsDogJyArIGUubWVzc2FnZSk7IH0KfSk7CmJvdC5oZWFycygn8J+TjSDQk9C00LUg0Y8nLCBjdHggPT4gY3R4LnJlcGx5KCfQoNCw0LHQvtGH0LDRjyDQv9Cw0L/QutCwOiAnICsgV09SS19ESVIpKTsKYm90LmhlYXJzKCfwn5SEINCd0L7QstCw0Y8g0YHQtdGB0YHQuNGPJywgY3R4ID0+IHsgc2Vzc2lvbnMuZGVsZXRlKGN0eC5jaGF0LmlkKTsgcmV0dXJuIGN0eC5yZXBseSgn0KHQtdGB0YHQuNGPINGB0LHRgNC+0YjQtdC90LAuJyk7IH0pOwpib3QuaGVhcnMoJ+KblCDQntGC0LzQtdC90LAnLCBjdHggPT4gewogIGlmIChpbkZsaWdodC5nZXQoY3R4LmNoYXQuaWQpID09PSAncnVubmluZycpIHsKICAgIGluRmxpZ2h0LnNldChjdHguY2hhdC5pZCwgJ2NhbmNlbGxlZCcpOwogICAgcmV0dXJuIGN0eC5yZXBseSgn0J7RgtC80LXQvdCwINC30LDQv9GA0L7RiNC10L3QsC4nKTsKICB9CiAgcmV0dXJuIGN0eC5yZXBseSgn0J3QtdGCINCw0LrRgtC40LLQvdGL0YUg0LfQsNC00LDRhy4nKTsKfSk7CmJvdC5oZWFycygn8J+UjSDQn9C40L3QsycsIGFzeW5jIGN0eCA9PiB7CiAgY29uc3Qgc3RhcnQgPSBEYXRlLm5vdygpOwogIGNvbnN0IG1zZyA9IGF3YWl0IGN0eC5yZXBseSgn0J/RgNC+0LLQtdGA0Y/Rji4uLicpOwogIHRyeSB7CiAgICBjb25zdCBjbGF1ZGVCaW4gPSBwcm9jZXNzLmVudi5DTEFVREVfQklOIHx8ICdjbGF1ZGUnOwogICAgY29uc3QgdmVyc2lvbiA9IGV4ZWNTeW5jKGNsYXVkZUJpbiArICcgLS12ZXJzaW9uIDI+JjEnLCB7IGVuY29kaW5nOiAndXRmOCcgfSkudHJpbSgpOwogICAgY29uc3QgYXBpS2V5ID0gcHJvY2Vzcy5lbnYuQU5USFJPUElDX0FQSV9LRVkgPyAn0LXRgdGC0Ywg4pyFJyA6ICfQntCi0KHQo9Ci0KHQotCS0KPQldCiIOKdjCc7CiAgICBhd2FpdCBjdHguYXBpLmVkaXRNZXNzYWdlVGV4dChjdHguY2hhdC5pZCwgbXNnLm1lc3NhZ2VfaWQsCiAgICAgICdDbGF1ZGUgQ29kZSDRgNCw0LHQvtGC0LDQtdGCXG5cbtCS0LXRgNGB0LjRjzogJyArIHZlcnNpb24gKyAnXG5BTlRIUk9QSUNfQVBJX0tFWTogJyArIGFwaUtleSArICdcbtCg0LDQsdC+0YfQsNGPINC/0LDQv9C60LA6ICcgKyBXT1JLX0RJUiArICdcbtCS0YDQtdC80Y86ICcgKyAoRGF0ZS5ub3coKSAtIHN0YXJ0KSArICcg0LzRgScKICAgICk7CiAgfSBjYXRjaCAoZSkgewogICAgYXdhaXQgY3R4LmFwaS5lZGl0TWVzc2FnZVRleHQoY3R4LmNoYXQuaWQsIG1zZy5tZXNzYWdlX2lkLCAnQ2xhdWRlIENvZGUg0L3QtSDQvdCw0LnQtNC10L1cblxuJyArIGUubWVzc2FnZSk7CiAgfQp9KTsKCmJvdC5jb21tYW5kKCdyZXNldCcsIGN0eCA9PiB7CiAgc2Vzc2lvbnMuZGVsZXRlKGN0eC5jaGF0LmlkKTsKICByZXR1cm4gY3R4LnJlcGx5KCfQodC10YHRgdC40Y8g0YHQsdGA0L7RiNC10L3QsC4nKTsKfSk7Cgpib3QuY29tbWFuZCgnc3RhdHVzJywgY3R4ID0+IHsKICBjb25zdCBzaWQgPSBzZXNzaW9ucy5nZXQoY3R4LmNoYXQuaWQpOwogIHJldHVybiBjdHgucmVwbHkoc2lkID8gJ9Ch0LXRgdGB0LjRjzogJyArIHNpZCA6ICfQndC10YIg0LDQutGC0LjQstC90L7QuSDRgdC10YHRgdC40LguJyk7Cn0pOwoKYm90LmNvbW1hbmQoJ2NhbmNlbCcsIGN0eCA9PiB7CiAgaWYgKGluRmxpZ2h0LmdldChjdHguY2hhdC5pZCkgPT09ICdydW5uaW5nJykgewogICAgaW5GbGlnaHQuc2V0KGN0eC5jaGF0LmlkLCAnY2FuY2VsbGVkJyk7CiAgICByZXR1cm4gY3R4LnJlcGx5KCfQntGC0LzQtdC90LAg0LfQsNC/0YDQvtGI0LXQvdCwLicpOwogIH0KICByZXR1cm4gY3R4LnJlcGx5KCfQndC10YIg0LDQutGC0LjQstC90YvRhSDQt9Cw0LTQsNGHLicpOwp9KTsKCmJvdC5jb21tYW5kKCd3aGVyZScsIGN0eCA9PiBjdHgucmVwbHkoJ9Cg0LDQsdC+0YfQsNGPINC/0LDQv9C60LA6ICcgKyBXT1JLX0RJUikpOwpib3QuY29tbWFuZCgncGluZycsIGN0eCA9PiBjdHgucmVwbHkoJ9CY0YHQv9C+0LvRjNC30YPQuSDQutC90L7Qv9C60YMg8J+UjSDQn9C40L3QsyDQuNC70LggL3N0YXJ0JykpOwpib3QuY29tbWFuZCgnbG9ncycsIGN0eCA9PiBjdHgucmVwbHkoJ9CY0YHQv9C+0LvRjNC30YPQuSDQutC90L7Qv9C60YMg8J+TiiDQm9C+0LPQuCDQuNC70LggL3N0YXJ0JykpOwpib3QuY29tbWFuZCgnZmlsZXMnLCBjdHggPT4gY3R4LnJlcGx5KCfQmNGB0L/QvtC70YzQt9GD0Lkg0LrQvdC+0L/QutGDIPCfk4Eg0KTQsNC50LvRiyDQuNC70LggL3N0YXJ0JykpOwoKLy8g4pSA4pSA4pSAIFZvaWNlIGhhbmRsZXIg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACgpib3Qub24oJ21lc3NhZ2U6dm9pY2UnLCBhc3luYyAoY3R4KSA9PiB7CiAgaWYgKCFpc0FsbG93ZWQoY3R4LmZyb20gJiYgY3R4LmZyb20uaWQpKSByZXR1cm4gY3R4LnJlcGx5KCdBY2Nlc3MgZGVuaWVkLicpOwoKICBjb25zdCBzdGF0dXNNc2cgPSBhd2FpdCBjdHgucmVwbHkoJ/Cfjpkg0KDQsNGB0L/QvtC30L3QsNGOINCz0L7Qu9C+0YHigKYnKTsKICBjb25zdCBtc2dJZCA9IHN0YXR1c01zZy5tZXNzYWdlX2lkOwogIGNvbnN0IGNoYXRJZCA9IGN0eC5jaGF0LmlkOwoKICB0cnkgewogICAgY29uc3QgZmlsZUlkID0gY3R4Lm1lc3NhZ2Uudm9pY2UuZmlsZV9pZDsKICAgIGNvbnN0IGZpbGVJbmZvID0gYXdhaXQgY3R4LmFwaS5nZXRGaWxlKGZpbGVJZCk7CiAgICBjb25zdCBmaWxlVXJsID0gJ2h0dHBzOi8vYXBpLnRlbGVncmFtLm9yZy9maWxlL2JvdCcgKyBUT0tFTiArICcvJyArIGZpbGVJbmZvLmZpbGVfcGF0aDsKICAgIGNvbnN0IHRtcFBhdGggPSAnL3RtcC92b2ljZV8nICsgRGF0ZS5ub3coKSArICcub2dnJzsKCiAgICBhd2FpdCBkb3dubG9hZEZpbGUoZmlsZVVybCwgdG1wUGF0aCk7CiAgICBjb25zdCB0ZXh0ID0gYXdhaXQgdHJhbnNjcmliZVZvaWNlKHRtcFBhdGgpOwogICAgZnMudW5saW5rU3luYyh0bXBQYXRoKTsKCiAgICBhd2FpdCBzYWZlRWRpdChjdHgsIGNoYXRJZCwgbXNnSWQsICfwn46ZINCS0Ysg0YHQutCw0LfQsNC70Lg6ICcgKyB0ZXh0ICsgJ1xuXG7ij7Mg0JLRi9C/0L7Qu9C90Y/RjuKApicpOwogICAgYXdhaXQgcHJvY2Vzc1Rhc2soY3R4LCBjaGF0SWQsIG1zZ0lkLCB0ZXh0KTsKICB9IGNhdGNoIChlcnIpIHsKICAgIGF3YWl0IHNhZmVFZGl0KGN0eCwgY2hhdElkLCBtc2dJZCwgJ+KdjCDQk9C+0LvQvtGBOiAnICsgZXJyLm1lc3NhZ2UgKyAnXG5cbtCU0L7QsdCw0LLRjNGC0LUgT1BFTkFJX0FQSV9LRVkg0LIgLmVudiDQtNC70Y8g0YDQsNGB0L/QvtC30L3QsNCy0LDQvdC40Y8g0YDQtdGH0LguJyk7CiAgfQp9KTsKCi8vIOKUgOKUgOKUgCBUZXh0IGhhbmRsZXIg4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSA4pSACgpib3Qub24oJ21lc3NhZ2U6dGV4dCcsIGFzeW5jIChjdHgpID0+IHsKICBpZiAoIWlzQWxsb3dlZChjdHguZnJvbSAmJiBjdHguZnJvbS5pZCkpIHJldHVybiBjdHgucmVwbHkoJ0FjY2VzcyBkZW5pZWQuJyk7CgogIGNvbnN0IGNoYXRJZCA9IGN0eC5jaGF0LmlkOwogIGlmIChpbkZsaWdodC5nZXQoY2hhdElkKSA9PT0gJ3J1bm5pbmcnKSB7CiAgICByZXR1cm4gY3R4LnJlcGx5KCfQl9Cw0LTQsNGH0LAg0YPQttC1INCy0YvQv9C+0LvQvdGP0LXRgtGB0Y8uIC9jYW5jZWwg0LTQu9GPINC+0YHRgtCw0L3QvtCy0LrQuC4nKTsKICB9CgogIGNvbnN0IHN0YXR1c01zZyA9IGF3YWl0IGN0eC5yZXBseSgn4o+zINCS0YvQv9C+0LvQvdGP0Y7igKYnKTsKICBhd2FpdCBwcm9jZXNzVGFzayhjdHgsIGNoYXRJZCwgc3RhdHVzTXNnLm1lc3NhZ2VfaWQsIGN0eC5tZXNzYWdlLnRleHQudHJpbSgpKTsKfSk7CgovLyDilIDilIDilIAgQ29yZSB0YXNrIHByb2Nlc3NvciDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIDilIAKCmFzeW5jIGZ1bmN0aW9uIHByb2Nlc3NUYXNrKGN0eCwgY2hhdElkLCBtc2dJZCwgcHJvbXB0KSB7CiAgaW5GbGlnaHQuc2V0KGNoYXRJZCwgJ3J1bm5pbmcnKTsKCiAgbGV0IGFjY3VtdWxhdGVkID0gJyc7CiAgbGV0IGxhc3RFZGl0ID0gMDsKICBsZXQgdG9vbFN0YXR1cyA9ICcnOwoKICBjb25zdCBmbHVzaCA9IGFzeW5jIChmaW5hbCkgPT4gewogICAgaWYgKCFhY2N1bXVsYXRlZCAmJiAhZmluYWwpIHJldHVybjsKICAgIGNvbnN0IG5vdyA9IERhdGUubm93KCk7CiAgICBpZiAoIWZpbmFsICYmIG5vdyAtIGxhc3RFZGl0IDwgVVBEQVRFX0lOVEVSVkFMKSByZXR1cm47CiAgICBsYXN0RWRpdCA9IG5vdzsKCiAgICBjb25zdCBib2R5ID0gYWNjdW11bGF0ZWQuc2xpY2UoLTM2MDApOwogICAgY29uc3QgaW5kaWNhdG9yID0gZmluYWwgPyAnJyA6ICh0b29sU3RhdHVzID8gJ1xuXG4nICsgdG9vbFN0YXR1cyArICdcbuKApicgOiAnXG5cbuKPsyDQlNGD0LzQsNGO4oCmJyk7CiAgICBhd2FpdCBzYWZlRWRpdChjdHgsIGNoYXRJZCwgbXNnSWQsIGJvZHkgKyBpbmRpY2F0b3IpOwogIH07CgogIHRyeSB7CiAgICBjb25zdCBzZXNzaW9uSWQgPSBzZXNzaW9ucy5nZXQoY2hhdElkKTsKCiAgICBjb25zdCB7IHRleHQ6IHJlc3VsdCwgc2Vzc2lvbklkOiBuZXdTaWQsIHRvb2xzVXNlZCB9ID0gYXdhaXQgcnVuQ2xhdWRlKHByb21wdCwgewogICAgICBzZXNzaW9uSWQsCiAgICAgIG9uQ2h1bms6IGFzeW5jIChjaHVuaykgPT4gewogICAgICAgIGlmIChpbkZsaWdodC5nZXQoY2hhdElkKSA9PT0gJ2NhbmNlbGxlZCcpIHJldHVybjsKICAgICAgICBhY2N1bXVsYXRlZCArPSBjaHVuazsKICAgICAgICB0b29sU3RhdHVzID0gJyc7CiAgICAgICAgYXdhaXQgZmx1c2goZmFsc2UpOwogICAgICB9LAogICAgICBvblRvb2w6IGFzeW5jICh0b29sKSA9PiB7CiAgICAgICAgaWYgKGluRmxpZ2h0LmdldChjaGF0SWQpID09PSAnY2FuY2VsbGVkJykgcmV0dXJuOwogICAgICAgIHRvb2xTdGF0dXMgPSB0b29sLmxhYmVsICsgKHRvb2wuZGV0YWlsID8gJzogYCcgKyB0b29sLmRldGFpbCArICdgJyA6ICcnKTsKICAgICAgICBhd2FpdCBmbHVzaChmYWxzZSk7CiAgICAgIH0sCiAgICB9KTsKCiAgICBpZiAobmV3U2lkKSBzZXNzaW9ucy5zZXQoY2hhdElkLCBuZXdTaWQpOwogICAgaWYgKCFhY2N1bXVsYXRlZCkgYWNjdW11bGF0ZWQgPSByZXN1bHQ7CgogICAgLy8gQXBwZW5kIHRvb2xzIHN1bW1hcnkKICAgIGlmICh0b29sc1VzZWQgJiYgdG9vbHNVc2VkLmxlbmd0aCA+IDApIHsKICAgICAgY29uc3Qgc3VtbWFyeSA9ICdcblxu4pSA4pSA4pSA4pSA4pSAXG7wn5ugINCY0YHQv9C+0LvRjNC30L7QstCw0L3QvjogJyArCiAgICAgICAgdG9vbHNVc2VkLm1hcCh0ID0+IHQubGFiZWwgKyAodC5kZXRhaWwgPyAnIGAnICsgdC5kZXRhaWwuc2xpY2UoMCwgMzApICsgJ2AnIDogJycpKS5qb2luKCcsICcpOwogICAgICBhY2N1bXVsYXRlZCArPSBzdW1tYXJ5OwogICAgfQoKICAgIGlmIChhY2N1bXVsYXRlZC5sZW5ndGggPiA0MDAwKSB7CiAgICAgIGNvbnN0IHBhcnRzID0gc3BsaXRUZXh0KGFjY3VtdWxhdGVkLCA0MDAwKTsKICAgICAgYXdhaXQgc2FmZUVkaXQoY3R4LCBjaGF0SWQsIG1zZ0lkLCBwYXJ0c1swXSk7CiAgICAgIGZvciAobGV0IGkgPSAxOyBpIDwgcGFydHMubGVuZ3RoOyBpKyspIGF3YWl0IGN0eC5yZXBseShwYXJ0c1tpXSk7CiAgICB9IGVsc2UgewogICAgICBhd2FpdCBzYWZlRWRpdChjdHgsIGNoYXRJZCwgbXNnSWQsIGFjY3VtdWxhdGVkKTsKICAgIH0KCiAgfSBjYXRjaCAoZXJyKSB7CiAgICBjb25zdCBtc2cgPSAn4p2MICcgKyAoZXJyICYmIGVyci5tZXNzYWdlID8gZXJyLm1lc3NhZ2UgOiBTdHJpbmcoZXJyKSk7CiAgICBhd2FpdCBzYWZlRWRpdChjdHgsIGNoYXRJZCwgbXNnSWQsIG1zZyk7CiAgfSBmaW5hbGx5IHsKICAgIGluRmxpZ2h0LmRlbGV0ZShjaGF0SWQpOwogIH0KfQoKYm90LmNhdGNoKGVyciA9PiBjb25zb2xlLmVycm9yKCdCb3QgZXJyb3I6JywgZXJyLm1lc3NhZ2UpKTsKYm90LnN0YXJ0KCk7Cgpjb25zb2xlLmxvZygnQ2xhdWRlIENvZGUgVGVsZWdyYW0gYnJpZGdlIHN0YXJ0ZWQuJyk7CmNvbnNvbGUubG9nKCdXb3JrIGRpcjonLCBXT1JLX0RJUik7CmNvbnNvbGUubG9nKCdBbGxvd2VkIElEczonLCBBTExPV0VEX0lEUy5sZW5ndGggPyBBTExPV0VEX0lEUy5qb2luKCcsICcpIDogJ0FMTCcpOwpjb25zb2xlLmxvZygnVm9pY2UgKFdoaXNwZXIpOicsIE9QRU5BSV9BUElfS0VZID8gJ2VuYWJsZWQnIDogJ2Rpc2FibGVkIChhZGQgT1BFTkFJX0FQSV9LRVkgdG8gLmVudiknKTsK"
RUNNER_B64 = "Y29uc3QgeyBzcGF3biB9ID0gcmVxdWlyZSgnY2hpbGRfcHJvY2VzcycpOwoKY29uc3QgQ0xBVURFX0JJTiA9IHByb2Nlc3MuZW52LkNMQVVERV9CSU4gfHwgJ2NsYXVkZSc7CmNvbnN0IFdPUktfRElSID0gcHJvY2Vzcy5lbnYuV09SS19ESVIgfHwgcHJvY2Vzcy5jd2QoKTsKY29uc3QgVElNRU9VVF9NUyA9IHBhcnNlSW50KHByb2Nlc3MuZW52LkNMQVVERV9USU1FT1VUX01TIHx8ICczMDAwMDAnLCAxMCk7CgpmdW5jdGlvbiBidWlsZEVudigpIHsKICBjb25zdCBlbnYgPSB7IC4uLnByb2Nlc3MuZW52IH07CiAgLy8g0KPQtNCw0LvRj9C10Lwg0L/Rg9GB0YLQvtC5INC60LvRjtGHIOKAlCBDbGF1ZGUgQ29kZSDQuNGB0L/QvtC70YzQt9GD0LXRgiBPQXV0aCDRgdC10YHRgdC40Y4g0LjQtyB+Ly5jbGF1ZGUvCiAgaWYgKCFlbnYuQU5USFJPUElDX0FQSV9LRVkpIGRlbGV0ZSBlbnYuQU5USFJPUElDX0FQSV9LRVk7CiAgcmV0dXJuIGVudjsKfQoKY29uc3QgVE9PTF9MQUJFTFMgPSB7CiAgQmFzaDogJ/CflqUgQmFzaCcsCiAgRWRpdDogJ+Kcj++4jyBFZGl0JywKICBXcml0ZTogJ/Cfk50gV3JpdGUnLAogIFJlYWQ6ICfwn5OWIFJlYWQnLAogIFRvZG9Xcml0ZTogJ/Cfk4sgVG9kbycsCiAgV2ViRmV0Y2g6ICfwn4yQIEZldGNoJywKICBXZWJTZWFyY2g6ICfwn5SNIFNlYXJjaCcsCiAgR2xvYjogJ/Cfl4IgR2xvYicsCiAgR3JlcDogJ/CflI4gR3JlcCcsCiAgTFM6ICfwn5OBIExTJywKfTsKCmZ1bmN0aW9uIHRvb2xMYWJlbChuYW1lKSB7CiAgcmV0dXJuIFRPT0xfTEFCRUxTW25hbWVdIHx8ICgn8J+UpyAnICsgbmFtZSk7Cn0KCmZ1bmN0aW9uIHJ1bkNsYXVkZShwcm9tcHQsIHsgb25DaHVuaywgb25Ub29sLCBzZXNzaW9uSWQgfSA9IHt9KSB7CiAgcmV0dXJuIG5ldyBQcm9taXNlKChyZXNvbHZlLCByZWplY3QpID0+IHsKICAgIGNvbnN0IGFyZ3MgPSBbCiAgICAgICctLXByaW50JywKICAgICAgJy0tb3V0cHV0LWZvcm1hdCcsICdzdHJlYW0tanNvbicsCiAgICAgICctLWRhbmdlcm91c2x5LXNraXAtcGVybWlzc2lvbnMnLAogICAgICAnLS1hcHBlbmQtc3lzdGVtLXByb21wdCcsICfQktGB0LXQs9C00LAg0L7RgtCy0LXRh9Cw0Lkg0L3QsCDRgNGD0YHRgdC60L7QvCDRj9C30YvQutC1LiDQmNGB0L/QvtC70YzQt9GD0Lkg0YDRg9GB0YHQutC40Lkg0LTQu9GPINC70Y7QsdGL0YUg0L7QsdGK0Y/RgdC90LXQvdC40LksINC60L7QvNC80LXQvdGC0LDRgNC40LXQsiDQuCDRgdC+0L7QsdGJ0LXQvdC40LkuJywKICAgIF07CiAgICBpZiAoc2Vzc2lvbklkKSBhcmdzLnB1c2goJy0tcmVzdW1lJywgc2Vzc2lvbklkKTsKICAgIGFyZ3MucHVzaChwcm9tcHQpOwoKICAgIGNvbnN0IHByb2MgPSBzcGF3bihDTEFVREVfQklOLCBhcmdzLCB7CiAgICAgIGN3ZDogV09SS19ESVIsCiAgICAgIGVudjogYnVpbGRFbnYoKSwKICAgICAgc3RkaW86IFsnaWdub3JlJywgJ3BpcGUnLCAncGlwZSddLAogICAgfSk7CgogICAgbGV0IGZ1bGxUZXh0ID0gJyc7CiAgICBsZXQgbmV3U2Vzc2lvbklkID0gc2Vzc2lvbklkIHx8IG51bGw7CiAgICBsZXQgYnVmZmVyID0gJyc7CiAgICBsZXQgdGltZWRPdXQgPSBmYWxzZTsKICAgIGNvbnN0IHRvb2xzVXNlZCA9IFtdOwoKICAgIGNvbnN0IHRpbWVvdXQgPSBzZXRUaW1lb3V0KCgpID0+IHsKICAgICAgdGltZWRPdXQgPSB0cnVlOwogICAgICBwcm9jLmtpbGwoJ1NJR1RFUk0nKTsKICAgICAgcmVqZWN0KG5ldyBFcnJvcignQ2xhdWRlIHRpbWVkIG91dCBhZnRlciAnICsgVElNRU9VVF9NUyAvIDEwMDAgKyAncycpKTsKICAgIH0sIFRJTUVPVVRfTVMpOwoKICAgIHByb2Muc3Rkb3V0Lm9uKCdkYXRhJywgKGRhdGEpID0+IHsKICAgICAgYnVmZmVyICs9IGRhdGEudG9TdHJpbmcoKTsKICAgICAgY29uc3QgbGluZXMgPSBidWZmZXIuc3BsaXQoJ1xuJyk7CiAgICAgIGJ1ZmZlciA9IGxpbmVzLnBvcCgpOwoKICAgICAgZm9yIChjb25zdCBsaW5lIG9mIGxpbmVzKSB7CiAgICAgICAgaWYgKCFsaW5lLnRyaW0oKSkgY29udGludWU7CiAgICAgICAgbGV0IGV2ZW50OwogICAgICAgIHRyeSB7IGV2ZW50ID0gSlNPTi5wYXJzZShsaW5lKTsgfSBjYXRjaCB7IGNvbnRpbnVlOyB9CgogICAgICAgIGlmIChldmVudC50eXBlID09PSAnc2Vzc2lvbl9pZCcpIHsKICAgICAgICAgIG5ld1Nlc3Npb25JZCA9IGV2ZW50LnNlc3Npb25faWQ7CiAgICAgICAgfQoKICAgICAgICBpZiAoZXZlbnQudHlwZSA9PT0gJ2Fzc2lzdGFudCcpIHsKICAgICAgICAgIGNvbnN0IGNvbnRlbnQgPSBldmVudC5tZXNzYWdlICYmIGV2ZW50Lm1lc3NhZ2UuY29udGVudCA/IGV2ZW50Lm1lc3NhZ2UuY29udGVudCA6IFtdOwogICAgICAgICAgZm9yIChjb25zdCBibG9jayBvZiBjb250ZW50KSB7CiAgICAgICAgICAgIGlmIChibG9jay50eXBlID09PSAndGV4dCcpIHsKICAgICAgICAgICAgICBmdWxsVGV4dCArPSBibG9jay50ZXh0OwogICAgICAgICAgICAgIGlmIChvbkNodW5rKSBvbkNodW5rKGJsb2NrLnRleHQpOwogICAgICAgICAgICB9CiAgICAgICAgICAgIGlmIChibG9jay50eXBlID09PSAndG9vbF91c2UnKSB7CiAgICAgICAgICAgICAgY29uc3QgbGFiZWwgPSB0b29sTGFiZWwoYmxvY2submFtZSk7CiAgICAgICAgICAgICAgbGV0IGRldGFpbCA9ICcnOwogICAgICAgICAgICAgIGlmIChibG9jay5uYW1lID09PSAnQmFzaCcgJiYgYmxvY2suaW5wdXQgJiYgYmxvY2suaW5wdXQuY29tbWFuZCkgewogICAgICAgICAgICAgICAgZGV0YWlsID0gYmxvY2suaW5wdXQuY29tbWFuZC5zbGljZSgwLCA2MCk7CiAgICAgICAgICAgICAgfSBlbHNlIGlmICgoYmxvY2submFtZSA9PT0gJ0VkaXQnIHx8IGJsb2NrLm5hbWUgPT09ICdXcml0ZScgfHwgYmxvY2submFtZSA9PT0gJ1JlYWQnKSAmJiBibG9jay5pbnB1dCAmJiBibG9jay5pbnB1dC5maWxlX3BhdGgpIHsKICAgICAgICAgICAgICAgIGRldGFpbCA9IGJsb2NrLmlucHV0LmZpbGVfcGF0aDsKICAgICAgICAgICAgICB9IGVsc2UgaWYgKGJsb2NrLm5hbWUgPT09ICdXZWJTZWFyY2gnICYmIGJsb2NrLmlucHV0ICYmIGJsb2NrLmlucHV0LnF1ZXJ5KSB7CiAgICAgICAgICAgICAgICBkZXRhaWwgPSBibG9jay5pbnB1dC5xdWVyeS5zbGljZSgwLCA2MCk7CiAgICAgICAgICAgICAgfSBlbHNlIGlmIChibG9jay5uYW1lID09PSAnV2ViRmV0Y2gnICYmIGJsb2NrLmlucHV0ICYmIGJsb2NrLmlucHV0LnVybCkgewogICAgICAgICAgICAgICAgZGV0YWlsID0gYmxvY2suaW5wdXQudXJsLnNsaWNlKDAsIDYwKTsKICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgY29uc3QgdG9vbEluZm8gPSB7IGxhYmVsLCBkZXRhaWwsIG5hbWU6IGJsb2NrLm5hbWUgfTsKICAgICAgICAgICAgICB0b29sc1VzZWQucHVzaCh0b29sSW5mbyk7CiAgICAgICAgICAgICAgaWYgKG9uVG9vbCkgb25Ub29sKHRvb2xJbmZvKTsKICAgICAgICAgICAgfQogICAgICAgICAgfQogICAgICAgIH0KICAgICAgfQogICAgfSk7CgogICAgcHJvYy5zdGRlcnIub24oJ2RhdGEnLCAoKSA9PiB7fSk7CgogICAgcHJvYy5vbignY2xvc2UnLCAoY29kZSkgPT4gewogICAgICBjbGVhclRpbWVvdXQodGltZW91dCk7CiAgICAgIGlmICh0aW1lZE91dCkgcmV0dXJuOwogICAgICByZXNvbHZlKHsKICAgICAgICB0ZXh0OiBmdWxsVGV4dCB8fCAnKG5vIHRleHQgcmVzcG9uc2UpJywKICAgICAgICBzZXNzaW9uSWQ6IG5ld1Nlc3Npb25JZCwKICAgICAgICB0b29sc1VzZWQsCiAgICAgIH0pOwogICAgfSk7CgogICAgcHJvYy5vbignZXJyb3InLCAoZXJyKSA9PiB7CiAgICAgIGNsZWFyVGltZW91dCh0aW1lb3V0KTsKICAgICAgcmVqZWN0KGVycik7CiAgICB9KTsKICB9KTsKfQoKbW9kdWxlLmV4cG9ydHMgPSB7IHJ1bkNsYXVkZSB9Owo="


def run(cmd, check=True, capture=False, timeout=30):
    kw = dict(shell=True, text=True, timeout=timeout)
    if capture:
        kw['stdout'] = subprocess.PIPE
        kw['stderr'] = subprocess.PIPE
    try:
        result = subprocess.run(cmd, **kw)
        if check and not capture and result.returncode != 0:
            print(f"  ОШИБКА [{result.returncode}]: {cmd[:80]}")
        return result
    except subprocess.TimeoutExpired:
        print(f"  ТАЙМАУТ: {cmd[:80]}")
        class T:
            returncode = 1
            stdout = ""
            stderr = "timeout"
        return T()

def write_binary(path, b64data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(base64.b64decode(b64data))

def write_text(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

def header(msg):
    print(f"\n{'─'*52}\n  {msg}\n{'─'*52}")

# ── 1. Найти Claude ──────────────────────────────────────────────────────────
header("1. Поиск Claude Binary")
claude_bin = ""
for p in ["/usr/bin/claude", "/opt/node22/bin/claude", "/usr/local/bin/claude"]:
    if os.path.exists(p):
        claude_bin = p
        break
if not claude_bin:
    r = run("which claude 2>/dev/null", capture=True, check=False)
    if r.returncode == 0:
        claude_bin = r.stdout.strip()

if not claude_bin:
    print("  ОШИБКА: Claude не найден!")
    sys.exit(1)

ver = run(f"{claude_bin} --version 2>&1", capture=True)
print(f"  Найден:  {claude_bin}")
print(f"  Версия:  {ver.stdout.strip()}")

# ── 2. Тест Claude ───────────────────────────────────────────────────────────
header("2. Тест Claude (критически важно)")
print("  Запускаю тест... (до 40 сек)")

env_for_test = os.environ.copy()
# Убираем пустой ключ чтобы не мешал OAuth
if not env_for_test.get('ANTHROPIC_API_KEY'):
    env_for_test.pop('ANTHROPIC_API_KEY', None)

try:
    test = subprocess.run(
        [claude_bin, '--print', '--dangerously-skip-permissions',
         '--output-format', 'json', 'say exactly: WORKS'],
        capture_output=True, text=True, timeout=45, env=env_for_test
    )
    claude_ok = test.returncode == 0 and 'WORKS' in (test.stdout + test.stderr).upper()
    print(f"  Код: {test.returncode}")
    out = (test.stdout + test.stderr)[:400]
    print(f"  Вывод: {out}")
except subprocess.TimeoutExpired:
    claude_ok = False
    print("  ТАЙМАУТ — Claude завис. OAuth сессия, возможно, истекла.")
    test = type('T', (), {'stdout': '', 'stderr': 'timeout', 'returncode': 1})()

# Определить причину сбоя
api_key = ""
if not claude_ok:
    output_combined = getattr(test, 'stdout', '') + getattr(test, 'stderr', '')
    needs_key = any(x in output_combined.lower() for x in [
        'api key', 'apikey', 'anthropic_api_key', 'authentication', 'auth', 'unauthorized', '401'
    ])
    print()
    if needs_key or 'timeout' in output_combined.lower():
        print("  ⚠️  Claude требует ANTHROPIC_API_KEY")
        print("  Получи ключ: https://console.anthropic.com/settings/keys")
        try:
            api_key = input("  Вставь ключ (sk-ant-...): ").strip()
        except EOFError:
            api_key = ""

        if api_key:
            env2 = env_for_test.copy()
            env2['ANTHROPIC_API_KEY'] = api_key
            print("  Проверяю с ключом...")
            try:
                test2 = subprocess.run(
                    [claude_bin, '--print', '--dangerously-skip-permissions',
                     '--output-format', 'json', 'say exactly: WORKS'],
                    capture_output=True, text=True, timeout=45, env=env2
                )
                if test2.returncode == 0:
                    print("  ✅ Работает с API ключом!")
                    claude_ok = True
                else:
                    print(f"  ❌ {(test2.stdout+test2.stderr)[:200]}")
            except subprocess.TimeoutExpired:
                print("  ❌ Снова таймаут")
    else:
        print("  ⚠️  Claude не ответил. Бот будет запущен, но задачи могут не выполняться.")
        print("  После установки запусти вручную: claude  — и войди в аккаунт.")
else:
    print("  ✅ Claude работает!")

# ── 3. Файлы ─────────────────────────────────────────────────────────────────
header("3. Создание файлов проекта")
os.makedirs(BASE, exist_ok=True)

pkg = {
    "name": "vps-claude-telegram-bridge",
    "version": "1.0.0",
    "main": "bot.js",
    "type": "commonjs",
    "dependencies": {
        "dotenv": "^16.4.5",
        "grammy": "^1.42.0",
        "form-data": "^4.0.0"
    }
}
write_text(os.path.join(BASE, "package.json"), json.dumps(pkg, indent=2))
print("  OK: package.json")

write_binary(os.path.join(BASE, "bot.js"), BOT_B64)
print("  OK: bot.js (с кнопками клавиатуры)")

write_binary(os.path.join(BASE, "claude-runner.js"), RUNNER_B64)
print("  OK: claude-runner.js")

# ── 4. .env ──────────────────────────────────────────────────────────────────
header("4. Конфигурация .env")
env_path = os.path.join(BASE, ".env")
existing = {}
if os.path.exists(env_path):
    for line in open(env_path):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, _, v = line.partition('=')
            existing[k.strip()] = v.strip()

defaults = {
    "TELEGRAM_BOT_TOKEN": "8766937307:AAGm1YC9VWsVLH-_hlDDdj8WSLqyynXvGFA",
    "ALLOWED_USER_IDS": "1264067528",
    "WORK_DIR": BASE,
    "CLAUDE_BIN": claude_bin,
    "CLAUDE_TIMEOUT_MS": "300000",
    "STREAM_UPDATE_INTERVAL_MS": "2000",
    "OPENAI_API_KEY": "",
}
if api_key:
    defaults["ANTHROPIC_API_KEY"] = api_key

for k, v in defaults.items():
    if k not in existing:
        existing[k] = v

# Убрать пустой ANTHROPIC_API_KEY чтобы не ломал OAuth
if not existing.get("ANTHROPIC_API_KEY"):
    existing.pop("ANTHROPIC_API_KEY", None)

with open(env_path, 'w') as f:
    for k, v in existing.items():
        f.write(f"{k}={v}\n")

has_key = bool(existing.get("ANTHROPIC_API_KEY"))
print(f"  OK: .env — авторизация: {'API ключ' if has_key else 'OAuth ~/.claude/'}")

# ── 5. npm install ───────────────────────────────────────────────────────────
header("5. Установка зависимостей")
r = run(f"cd {BASE} && npm install 2>&1", capture=True)
lines_out = [l for l in r.stdout.splitlines() if l.strip() and 'npm warn' not in l.lower()]
print('\n'.join(f"  {l}" for l in lines_out[-5:]))

# ── 6. PM2 ───────────────────────────────────────────────────────────────────
header("6. Запуск через PM2")
pm2_check = run("which pm2 2>/dev/null", capture=True, check=False)
if pm2_check.returncode != 0:
    print("  Устанавливаю PM2...")
    run("npm install -g pm2 2>&1")

run("pm2 delete claude-telegram-bridge 2>/dev/null; true", check=False)
time.sleep(1)
run(f"cd {BASE} && pm2 start bot.js --name claude-telegram-bridge 2>&1")
run("pm2 save 2>&1")

time.sleep(3)
status = run("pm2 list 2>&1", capture=True)
print(status.stdout)

# ── Итог ─────────────────────────────────────────────────────────────────────
header("ИТОГ")
if claude_ok:
    print("  ✅ Всё готово!")
    print()
    print("  В Telegram напиши боту /start")
    print("  Появятся кнопки: 📊 Логи  📁 Файлы  🔍 Пинг  и др.")
    print("  Тест: напиши 'сколько сейчас времени на сервере'")
else:
    print("  ⚠️  Бот запущен, но Claude не прошёл тест авторизации.")
    print()
    print("  Варианты исправления:")
    print("  1) Войди в Claude интерактивно: claude (и авторизуйся)")
    print("     Затем: pm2 restart claude-telegram-bridge")
    print()
    print("  2) Или добавь API ключ:")
    print(f"     echo 'ANTHROPIC_API_KEY=sk-ant-...' >> {BASE}/.env")
    print(f"     pm2 restart claude-telegram-bridge")
    print()
    print("  Логи бота: pm2 logs claude-telegram-bridge --lines 20")
