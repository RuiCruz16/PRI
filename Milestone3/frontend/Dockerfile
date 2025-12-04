# Use Node.js for building and running
FROM node:24-alpine

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the code
COPY . .

# Expose the Vite port
EXPOSE 5173

# Start the app with --host to expose it to the network
CMD ["npm", "run", "dev", "--", "--host"]