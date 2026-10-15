import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({

    plugins: [
        react()
    ],

    server: {

        proxy: {

            "/chat": {

                target: "http://172.18.0.1:8000",

                changeOrigin: true

            },

            "/database": {

                target: "http://172.18.0.1:8000",

                changeOrigin: true

            }

        }

    }

});
