function process_message()
    local payload = read_message('Payload')

    inject_payload("json", "server_db", payload)

    return 0
end
