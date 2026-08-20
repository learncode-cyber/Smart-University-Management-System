# NOTE: runs the Vite DEV server, not a production build. Chosen deliberately
# for this academic submission — vite.config.ts already proxies /api to the
# backend container by hostname (see docker-compose.yml), so `npm run dev`
# "just works" for a grader with one command. A real production deployment
# should instead build a static bundle (`npm run build`) and serve it behind
# a reverse proxy (nginx/Caddy) that forwards /api — flagged as a Part 11
# hardening step, not done here to keep the submission package simple.
FROM node:20-slim
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
