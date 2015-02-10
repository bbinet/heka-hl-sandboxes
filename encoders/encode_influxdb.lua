function process_message()
    inject_payload('json', 'influxdb', read_message('Payload'))

    return 0
end
