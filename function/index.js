const AWS = require("aws-sdk");
const client = new AWS.S3();
exports.handler = async (event) => {
    console.log(JSON.stringify(event));

    try {
    } catch (error) {
        console.log(error);
        throw new Error("Error occurred while writing to S3");
    }
};