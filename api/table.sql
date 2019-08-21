CREATE TABLE public.scheduled_jobs (
			id SERIAL PRIMARY KEY,
			job_id character varying(100) NOT NULL,
			status character varying(15),
			input_url character varying(3000),
			output_path character varying(1000),
			start_time timestamp without time zone,
			updated_time timestamp without time zone,
			end_time timestamp without time zone,
			total_file_size BIGINT,
			downloaded_size BIGINT,
			remaining_size  BIGINT,
			command character varying(500)
);