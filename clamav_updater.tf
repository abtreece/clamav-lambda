resource "aws_security_group" "clamav-updates" {
    name = "clamav-updates"
    description = "Rules allowing egress for ClamAV updates - Lambda controlled"
    vpc_id = ""

    tags {
      Name = "clamav-updates"
    }
}

data "archive_file" "clamav-updater-zip" {
    type = "zip"
    source_file = "${path.module}/lambda_functions/clamav_updater.py"
    output_path = "${path.module}/.terraform/archive_files/clamav_updater.zip"
}

resource "aws_lambda_function" "clamav-updater" {
    function_name = "clamav_updater"
    handler = "clamav_updater.lambda_handler"
    role = "${aws_iam_role.lambda-security-group-update.arn}"
    runtime = "python2.7"
    filename = "${data.archive_file.clamav-updater-zip.output_path}"
    source_code_hash = "${data.archive_file.clamav-updater-zip.output_base64sha256}"
}

resource "aws_lambda_permission" "allow_cloudwatch_trigger" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = "${aws_lambda_function.clamav-updater.function_name}"
    principal = "events.amazonaws.com"
    source_arn = "${aws_cloudwatch_event_rule.clamav-updater-event.arn}"
}

resource "aws_cloudwatch_event_rule" "clamav-updater-event" {
    name = "clamav-updater-event"
    description = "Scheduled update of ClamAV Security Group rules"
    schedule_expression = "cron(0 */3 ? * * *)"
}

resource "aws_cloudwatch_event_target" "clamav-updater-event-target" {
    target_id = "clamav-updater-event-target"
    rule = "${aws_cloudwatch_event_rule.clamav-updater-event.name}"
    arn = "${aws_lambda_function.clamav-updater.arn}"
}
