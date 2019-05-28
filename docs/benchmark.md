# Benchmarking

Omnibus also supports benchmarking using PyCurl to obtain following metrics :


#### Name Lookup Time:
- Parameter : namelookup_time
- Description : Receive the total time in seconds from the start until the name resolving was completed. 

#### App Connect Time:
- Parameter : appconnect_time
- Description : Receive the time, in seconds, it took from the start until the SSL/SSH connect/handshake to the remote host was completed.

#### Pre Transfer Time:
- Parameter : pretransfer_time
- Description : receive the time, in seconds, it took from the start until the file transfer is just about to begin. This includes all pre-transfer commands and negotiations that are specific to the particular protocol(s) involved. It does not involve the sending of the protocol- specific request that triggers a transfer.

#### Start Transfer Time:
- Parameter: starttransfer_time
- Description : receive the time, in seconds, it took from the start until the first byte is received by libcurl. This includes CURLINFO_PRETRANSFER_TIME and also the time the server needs to calculate the result. 

#### Redirect Time:
- Parameter : redirect_time
- Description : receive the total time, in seconds, it took for all redirection steps include name lookup, connect, pretransfer and transfer before final transaction was started. CURLINFO_REDIRECT_TIME contains the complete execution time for multiple redirections. 

#### Total Time:
- Parameter : total_time
- Description : receive the total time in seconds for the previous transfer, including name resolving, TCP connect etc. The double represents the time in seconds, including fractions. 

#### Size Download :
- Parameter : size_download
- Description : receive the total amount of bytes that were downloaded. The amount is only for the latest transfer and will be reset again for each new transfer. This counts actual payload data, what's also commonly called body. All meta and header data are excluded and will not be counted in this number. 

#### Size Upload :
- Parameter : size_upload
- Description : receive the total amount of bytes that were uploaded. 

#### Request Size :
- Parameter : request_size
- Description : Receive the total size of the issued requests. This is so far only for HTTP requests.

#### Speed Download :
- Parameter : speed_download
- Description : Receive the average download speed that curl measured for the complete download. Measured in bytes/second. 

#### Speed Upload :
- Parameter : speed_upload
- Description : Receive the average upload speed that curl measured for the complete upload. Measured in bytes/second. 

#### Redirect Count :
- Parameter : redirect_count
- Description : Receive the total number of redirections that were actually followed. 

#### Num Connects:
- Parameter : receive how many new connections libcurl had to create to achieve the previous transfer (only the successful connects are counted). Combined with _**redirect_count**_ you are able to know how many times libcurl successfully reused existing connection(s) or not.


## Aggregates:
Obtained metrics can also be processed using following aggregates :

- **mean_arithmetic** : Standard average value
- **mean** : an alias for mean_arithmetic
- **mean_harmonic** : Harmonic mean or subcontrary mean, appropriate when average of rates is desired
- **median** : Middle value of results
- **std_deviation** : Result spread compared to average
- **sum** : Total Value
- **total** : Total Value



## Concurrency and Benchmark Run:
Omnibus also supports concurrent request. 200 benchmark runs with 10 concurrency means that omnibus will make 200/10 = 20 concurrent requests. 


## Reports :
Currenty Benchmark and Tests is reported separately. A test file with benchmark inside will only generate a benchmark reports. Separating benchmarking and blackbox testing is advisable. 

## Example :
```yaml
- config:
  - desc: configuration for test set
  - testset: "TTL Endpoint"
  - scope: configuration working scope
  - group: "TTL Endpoint"
  - url: "http://127.0.0.1:6968/"
  - endpoint: "api/ttl"
  - generator: 
    - dnslist : {type : random_text, length: 5}

- benchmark: # create entity
  - name: "Test Post"
  - endpoint: "api/zone"
  - method: 'GET'
  - generator_binds: { nm_zone: dnslist}
  - headers: {template: {'Content-Type': 'application/json'}}
  - benchmark_runs: '200'
  - concurrency : 10
  - extract_binds:
      - id_ttl: {jmespath: 'message.id'}
  - metrics:
    - total_time
    - total_time: mean
    - total_time: median
    - size_download
    - speed_download
```

Configuration above will measure total time, size download and speed download of each concurrent requests.




## Further Read:
- [PyCurl.INFO](https://curl.haxx.se/libcurl/c/easy_getinfo_options.html) : Further information on measurement available on Pycurl
- [Back to Readme](../README.md)