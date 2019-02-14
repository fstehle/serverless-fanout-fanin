# serverless-fanout-fanin

Example showcase project for a serverless fan-out & fan-in solution using AWS Lambda, SQS & DynamoDB.

## Architecture

TBD (see code for the moment)

## Deployment

```
make deploy
```

## Triggering the ventilator

```
node_modules/.bin/serverless invoke -f ventilator
```

## Watching the logs

Use different tabs for viewing the logs of each function:

```
node_modules/.bin/serverless logs -f ventilator -t
node_modules/.bin/serverless logs -f worker -t
node_modules/.bin/serverless logs -f sink -t
```