resource "aws_iam_role" "lambda-security-group-update" {
    name = "lambda-security-group-update"
    assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

data "aws_iam_policy_document" "allow-lambda-to-update-sg" {
    statement {
        actions = [
            "ec2:DescribeSecurityGroups",
            "ec2:AuthorizeSecurityGroupEgress",
            "ec2:RevokeSecurityGroupEgress",
        ]
        resources = [
            "*",
        ]
    }
}

resource "aws_iam_policy" "lambda-security-group-update" {
    name = "lamdba-security-group-update"
    path = "/"
    policy = "${data.aws_iam_policy_document.allow-lambda-to-update-sg.json}"
}

resource "aws_iam_role_policy_attachment" "attach-sg-update-policy" {
    role       = "${aws_iam_role.lambda-security-group-update.name}"
    policy_arn = "${aws_iam_policy.lambda-security-group-update.arn}"
}

resource "aws_iam_role_policy_attachment" "basic-exec-role" {
    role       = "${aws_iam_role.lambda-security-group-update.name}"
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
