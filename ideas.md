
 /kestro/sensors/<name>/output/value


all changes will be send to mqtt broker
the peripheral service will also listen to all
/kestro/sensors/# and update a local properties map with the information

any kestro-iot service can then use this information to update a display ...


This approach means we can't update the template of a display and it will be fixed

So, should we allow to update the display templates dynamically ???
we could set a default text, but this means that the text_template must also be 
updated via REST or maybe mqtt.
--> /kestro/displays/<name>/template
