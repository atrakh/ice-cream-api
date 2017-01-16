# ice-cream-api
<h4>RESTful API built on Flask, using LaunchDarkly feature flags to serve rate limits.</h4>

Want to test out this API? There's a live demo available!

Try entering these commands in a terminal evironment to make an API request. <b>Note</b>: Replace text in capitals with desired resource/field

<b>Get all flavors:</b> 
<code>$ curl -v http://atrakh.com/api/v1/flavors</code>

<b>Get a specific flavor:</b>
<code>$ curl -v http://atrakh.com/api/v1/flavors/FLAVOR_NAME</code>


<b>Create a new flavor:</b>
<code>$ curl -v -H "Content-Type: application/json" -X POST -d
'{"name":FLAVOR_NAME, "stock":FLAVOR_AMOUNT}' http://atrakh.com/api/v1/flavors</code>

<b>Create an existing flavor:</b>
<code>$ curl -v -H "Content-Type: application/json" -X PUT -d
'{"name":NEW_FLAVOR_NAME, "stock":NEW_FLAVOR_AMOUNT}' http://atrakh.com/api/v1/flavors/FLAVOR_NAME</code>

<b>Delete a flavor:</b>
<code>$ curl -v -X DELETE http://atrakh.com/api/v1/flavors/FLAVOR_NAME</code>
