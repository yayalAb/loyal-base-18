FROM odoo:18

USER root


# Create necessary directories
RUN mkdir -p /etc/odoo/theme /etc/odoo/hr /etc/odoo/addons /etc/odoo/accounting /etc/odoo/addons_e /etc/odoo/inv_purchase_sales /etc/odoo/project /etc/odoo/fleet /etc/odoo/pos /etc/odoo/documents

# Copy files into the image
COPY ./theme /etc/odoo/theme
COPY ./hr /etc/odoo/hr
COPY ./addons /etc/odoo/addons
COPY ./addons_e /etc/odoo/addons_e
COPY ./inv_purchase_sales /etc/odoo/inv_purchase_sales
COPY ./project /etc/odoo/project
COPY ./fleet /etc/odoo/fleet
COPY ./pos /etc/odoo/pos
COPY ./documents /etc/odoo/documents
COPY ./etc /etc/odoo


# Install python3-venv and create a virtual environment
# RUN apt-get update && apt-get install -y python3-venv && \
#     python3 -m venv /venv && \
#     /venv/bin/pip install --upgrade pip

# Install Python packages in the virtual environment
RUN pip install pandas num2words abyssinica email-validator opencv-python python-barcode --break-system-packages
RUN pip install --ignore-installed typing-extensions pydantic opencv-python --break-system-packages


# Set the PATH to use the virtual environment
ENV PATH="/venv/bin:$PATH"

# Expose the Odoo port
EXPOSE 8069

# Set the entry point for the container
ENTRYPOINT ["odoo", "-c", "/etc/odoo/odoo.conf"]
