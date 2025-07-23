# CareSetu Voice Agent - Frontend Example

This is a simple example of how to integrate your CareSetu Voice Agent with a web frontend using LiveKit.

## Getting Started

1. **Update LiveKit Configuration**

   Open `index.html` and update the LiveKit configuration:

   ```javascript
   const LIVEKIT_URL = "YOUR_LIVEKIT_URL"; // Replace with your LiveKit URL
   const TOKEN = "YOUR_TOKEN"; // You'll need to generate this on your server
   ```

2. **Generate a Token**

   You'll need to generate a LiveKit token on your server. Here's a simple example using Node.js:

   ```javascript
   const { AccessToken } = require("livekit-server-sdk");

   // Create a new token
   const token = new AccessToken("YOUR_API_KEY", "YOUR_API_SECRET", {
     identity: "user-123", // Unique user identifier
     name: "User Name", // Display name
   });

   // Grant permissions
   token.addGrant({
     roomJoin: true,
     room: "room-name",
     canPublish: true,
     canSubscribe: true,
   });

   // Generate the token
   const jwt = token.toJwt();
   console.log(jwt);
   ```

3. **Run the Example**

   You can run this example using any web server. For a simple option, use Python's built-in HTTP server:

   ```bash
   # Python 3
   python -m http.server 8000
   ```

   Then open `http://localhost:8000` in your browser.

## Integration with Your Backend

In a production environment, you should:

1. Generate tokens on your server
2. Implement proper user authentication
3. Create rooms dynamically for each user session
4. Handle reconnection logic
5. Add error handling and fallbacks

## LiveKit Documentation

For more information on LiveKit integration, see:

- [LiveKit Client SDK Documentation](https://docs.livekit.io/client-sdk-js/)
- [LiveKit Server SDK Documentation](https://docs.livekit.io/server-sdk-js/)

## Next Steps

1. Implement proper token generation on your server
2. Add error handling and reconnection logic
3. Enhance the UI with your branding
4. Add features like appointment booking forms
5. Implement analytics and logging
