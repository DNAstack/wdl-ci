version 1.0

# Validate input FASTA files
# Input type: FASTA file

task fasta_validator {
	input {
		File current_run_output
		File validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		if gzip -t ~{current_run_output}; then
			dir_path=$(dirname ~{current_run_output})
			gzip -d ~{current_run_output} ~{validated_output}
			if ! fasta_validate -v "${dir_path}/$(basename ~{validated_output} .gz)"; then
				err "Validated FASTA: [~{basename(validated_output)}] is not valid; check format"
				exit 1
			else
				if ! fasta_validate -v "${dir_path}/$(basename ~{current_run_output} .gz)"; then
					err "Current FASTA: [~{basename(current_run_output)}] is not valid"
					exit 1
				else
					echo "Current FASTA: [~{basename(current_run_output)}] is valid"
				fi
			fi
		else
			if ! fasta_validate -v ~{validated_output}; then
				err "Validated FASTA: [~{basename(validated_output)}] is not valid; check format"
				exit 1
			else
				if ! fasta_validate -v ~{current_run_output}; then
					err "Current FASTA: [~{basename(current_run_output)}] is not valid"
					exit 1
				else
					echo "Current FASTA: [~{basename(current_run_output)}] is valid"
				fi
			fi			
		fi
	>>>

	output {
		#Int rc = read_int("rc")
	}

	runtime {
		docker: "kfang4/fasta_validator:latest"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}